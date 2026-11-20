"""Aplicación Flask de cadenas de Markov."""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from . import __version__
from .config import DESCRIPCION_ESTADOS, PASOS_REQUERIDOS
from .db import (
    DEFAULT_DATABASE_PATH,
    ScenarioExistsError,
    ensure_database,
    get_scenario,
    healthcheck,
    list_history,
    list_scenarios,
    save_calculation,
    save_scenario,
)
from .markov import ValidationError, compute_all, default_scenario


def _db_path() -> str:
    from flask import current_app

    return str(current_app.config["DATABASE_PATH"])


def _a_flotante(valor: object, campo: str) -> float:
    if isinstance(valor, str):
        valor = valor.strip().replace(",", ".")
    try:
        return float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{campo} debe ser un número.") from error


def _entero(valor: object, campo: str) -> int:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError) as error:
        raise ValidationError(f"{campo} debe ser un número entero.") from error


def _resultado_desde_formulario(form) -> tuple[dict, str]:
    n_estados = _entero(form.get("n_estados", 3), "El número de estados")
    if not 3 <= n_estados <= 6:
        raise ValidationError("La cadena debe tener entre 3 y 6 estados.")

    estados = []
    for i in range(n_estados):
        estado = form.get(f"e_{i}", "").strip()
        if not estado:
            raise ValidationError(f"El estado {i + 1} debe tener un nombre.")
        estados.append(estado)

    matriz = []
    for i in range(n_estados):
        fila = []
        for j in range(n_estados):
            fila.append(
                _a_flotante(
                    form.get(f"m_{i}_{j}", ""),
                    f"La probabilidad de la fila {i + 1}, columna {j + 1}",
                )
            )
        matriz.append(fila)

    inicial = [
        _a_flotante(
            form.get(f"p_{i}", ""), f"La probabilidad inicial del estado {i + 1}"
        )
        for i in range(n_estados)
    ]

    pasos = form.get("pasos_personalizados", "")
    resultado = compute_all(estados, matriz, inicial, pasos)
    return resultado, pasos


def _contexto(
    resultado: dict | None = None,
    error: str | None = None,
    pasos_personalizados: str = "",
    escenario_id: int | None = None,
) -> dict:
    ruta = _db_path()
    escenarios = list_scenarios(ruta)
    historial = list_history(10, ruta)
    if resultado is None:
        resultado = default_scenario()

    return {
        "resultado": resultado,
        "estados": resultado["estados"],
        "matriz": resultado["matriz"],
        "distribucion_inicial": resultado["distribucion_inicial"],
        "pasos_requeridos": list(PASOS_REQUERIDOS),
        "pasos_personalizados": pasos_personalizados,
        "estacionaria": resultado["estacionaria"],
        "error": error,
        "escenarios": escenarios,
        "historial": historial,
        "escenario_id": escenario_id,
        "descripcion_estados": DESCRIPCION_ESTADOS,
        "version": __version__,
    }


def _escenario_id_valido(valor: object) -> int | None:
    try:
        escenario_id = int(str(valor))
    except (TypeError, ValueError):
        return None
    if escenario_id <= 0 or get_scenario(escenario_id, _db_path()) is None:
        return None
    return escenario_id


def create_app(config: dict | None = None) -> Flask:
    """Crea la aplicación Flask y prepara la base de datos."""

    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "clave-de-desarrollo"),
        DATABASE_PATH=os.environ.get("DATABASE_PATH", str(DEFAULT_DATABASE_PATH)),
        APP_ENV=os.environ.get("APP_ENV", "development"),
        MAX_CONTENT_LENGTH=1_048_576,
    )
    if config:
        app.config.update(config)

    ensure_database(app.config["DATABASE_PATH"])

    app.jinja_env.filters["prob"] = lambda valor: f"{float(valor):.4f}"

    @app.get("/")
    def index():
        escenario_id = _escenario_id_valido(request.args.get("escenario"))
        resultado = None
        if escenario_id is not None:
            escenario = get_scenario(escenario_id, _db_path())
            if escenario is not None:
                resultado = compute_all(
                    escenario["estados"],
                    escenario["matriz"],
                    escenario["distribucion_inicial"],
                )
        return render_template(
            "index.html",
            **_contexto(resultado, escenario_id=escenario_id),
        )

    @app.post("/calcular")
    def calcular():
        try:
            resultado, pasos = _resultado_desde_formulario(request.form)
            escenario_id = _escenario_id_valido(request.form.get("escenario_id"))
            save_calculation(
                resultado["resultados"],
                resultado["estacionaria"],
                escenario_id,
                _db_path(),
            )
            return render_template(
                "index.html",
                **_contexto(
                    resultado,
                    pasos_personalizados=pasos,
                    escenario_id=escenario_id,
                ),
            )
        except ValidationError as error:
            return (
                render_template(
                    "index.html",
                    **_contexto(
                        error=str(error),
                        pasos_personalizados=request.form.get(
                            "pasos_personalizados", ""
                        ),
                    ),
                ),
                400,
            )

    @app.post("/api/calcular")
    def api_calcular():
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            return jsonify({"ok": False, "error": "El cuerpo debe ser JSON."}), 400

        try:
            resultado = compute_all(
                datos.get("estados"),
                datos.get("matriz"),
                datos.get("distribucion_inicial"),
                datos.get("pasos_personalizados"),
            )
            escenario_id = _escenario_id_valido(datos.get("escenario_id"))
            save_calculation(
                resultado["resultados"],
                resultado["estacionaria"],
                escenario_id,
                _db_path(),
            )
            return jsonify({"ok": True, "resultado": resultado})
        except ValidationError as error:
            return jsonify({"ok": False, "error": str(error)}), 400

    @app.get("/api/escenarios")
    def api_escenarios():
        return jsonify({"ok": True, "escenarios": list_scenarios(_db_path())})

    @app.post("/api/escenarios")
    def api_guardar_escenario():
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            return jsonify({"ok": False, "error": "El cuerpo debe ser JSON."}), 400
        try:
            escenario = save_scenario(
                datos.get("nombre"),
                datos.get("estados"),
                datos.get("matriz"),
                datos.get("distribucion_inicial"),
                _db_path(),
            )
            return jsonify({"ok": True, "escenario": escenario}), 201
        except ScenarioExistsError as error:
            return jsonify({"ok": False, "error": str(error)}), 409
        except ValidationError as error:
            return jsonify({"ok": False, "error": str(error)}), 400

    @app.get("/api/escenarios/<int:escenario_id>")
    def api_escenario(escenario_id: int):
        escenario = get_scenario(escenario_id, _db_path())
        if escenario is None:
            return jsonify({"ok": False, "error": "Escenario no encontrado."}), 404
        return jsonify({"ok": True, "escenario": escenario})

    @app.get("/api/historial")
    def api_historial():
        limite = request.args.get("limite", "10")
        try:
            limite_entero = int(limite)
        except ValueError:
            return jsonify({"ok": False, "error": "El límite debe ser un entero."}), 400
        return jsonify({"ok": True, "historial": list_history(limite_entero, _db_path())})

    @app.get("/api/salud")
    def api_salud():
        try:
            estado_bd = healthcheck(_db_path())
        except Exception as error:  # pragma: no cover - depende del entorno
            return (
                jsonify(
                    {
                        "estado": "error",
                        "app": __version__,
                        "error": str(error),
                    }
                ),
                503,
            )
        return jsonify(
            {
                "estado": "ok",
                "app": __version__,
                "base_de_datos": estado_bd,
            }
        )

    return app
