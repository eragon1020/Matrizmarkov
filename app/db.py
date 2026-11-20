"""Persistencia SQLite para escenarios e historial de cálculos."""

from __future__ import annotations

import json
import os
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .config import (
    DISTRIBUCION_POR_DEFECTO,
    ESTADOS_POR_DEFECTO,
    MATRIZ_POR_DEFECTO,
    NOMBRE_ESCENARIO_POR_DEFECTO,
)
from .markov import ValidationError, validate_distribution, validate_matrix, validate_states

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "markov.db"


class ScenarioExistsError(ValidationError):
    """El nombre del escenario ya está registrado."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS escenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL COLLATE NOCASE,
    nombre_normalizado TEXT NOT NULL UNIQUE,
    estados TEXT NOT NULL,
    matriz TEXT NOT NULL,
    distribucion_inicial TEXT NOT NULL,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calculos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id INTEGER,
    pasos TEXT NOT NULL,
    resultados TEXT NOT NULL,
    estacionaria TEXT NOT NULL,
    creado_en TEXT NOT NULL,
    FOREIGN KEY (escenario_id) REFERENCES escenarios(id)
);
"""


def resolve_database_path(ruta: str | os.PathLike[str] | None = None) -> Path:
    """Resuelve la ruta de la base de datos desde un argumento o el entorno."""

    if ruta is None:
        ruta = os.environ.get("DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
    return Path(ruta).expanduser()


def connect(ruta: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    """Abre una conexión SQLite configurada para baja concurrencia."""

    destino = resolve_database_path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(str(destino), timeout=5.0)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA journal_mode=WAL")
    conexion.execute("PRAGMA busy_timeout=5000")
    conexion.execute("PRAGMA foreign_keys=ON")
    return conexion


@contextmanager
def _conexion(ruta: str | os.PathLike[str] | None = None):
    """Abre una conexión, confirma los cambios y la cierra siempre."""

    conexion = connect(ruta)
    try:
        yield conexion
        conexion.commit()
    finally:
        conexion.close()


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalizar_nombre(nombre: str) -> str:
    """Normaliza un nombre para compararlo sin distinguir mayúsculas ni acentos."""

    return unicodedata.normalize("NFKC", nombre).strip().casefold()


def _migrar_esquema(conexion: sqlite3.Connection) -> None:
    """Añade la columna normalizada a bases creadas con una versión anterior."""

    columnas = {
        fila["name"] for fila in conexion.execute("PRAGMA table_info(escenarios)")
    }
    if "nombre_normalizado" in columnas:
        return

    conexion.execute("ALTER TABLE escenarios ADD COLUMN nombre_normalizado TEXT")
    filas = conexion.execute("SELECT id, nombre FROM escenarios").fetchall()
    for fila in filas:
        conexion.execute(
            "UPDATE escenarios SET nombre_normalizado = ? WHERE id = ?",
            (_normalizar_nombre(fila["nombre"]), fila["id"]),
        )
    conexion.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_escenarios_nombre_normalizado "
        "ON escenarios(nombre_normalizado)"
    )


def init_db(ruta: str | os.PathLike[str] | None = None) -> None:
    """Crea las tablas si no existen y aplica migraciones simples."""

    with _conexion(ruta) as conexion:
        conexion.executescript(SCHEMA)
        _migrar_esquema(conexion)


def seed_default_scenario(ruta: str | os.PathLike[str] | None = None) -> None:
    """Inserta el escenario por defecto de forma idempotente."""

    with _conexion(ruta) as conexion:
        conexion.execute(
            """
            INSERT OR IGNORE INTO escenarios
                (nombre, nombre_normalizado, estados, matriz, distribucion_inicial, creado_en)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                NOMBRE_ESCENARIO_POR_DEFECTO,
                _normalizar_nombre(NOMBRE_ESCENARIO_POR_DEFECTO),
                json.dumps(ESTADOS_POR_DEFECTO, ensure_ascii=False),
                json.dumps(MATRIZ_POR_DEFECTO),
                json.dumps(DISTRIBUCION_POR_DEFECTO),
                _ahora(),
            ),
        )


def ensure_database(ruta: str | os.PathLike[str] | None = None) -> None:
    """Inicializa el esquema y siembra el escenario por defecto."""

    init_db(ruta)
    seed_default_scenario(ruta)


def _fila_a_escenario(fila: sqlite3.Row) -> dict:
    return {
        "id": fila["id"],
        "nombre": fila["nombre"],
        "estados": json.loads(fila["estados"]),
        "matriz": json.loads(fila["matriz"]),
        "distribucion_inicial": json.loads(fila["distribucion_inicial"]),
        "creado_en": fila["creado_en"],
    }


def list_scenarios(ruta: str | os.PathLike[str] | None = None) -> list[dict]:
    """Lista los escenarios guardados."""

    with _conexion(ruta) as conexion:
        filas = conexion.execute(
            "SELECT * FROM escenarios ORDER BY id ASC"
        ).fetchall()
    return [_fila_a_escenario(fila) for fila in filas]


def get_scenario(
    escenario_id: int, ruta: str | os.PathLike[str] | None = None
) -> dict | None:
    """Recupera un escenario por identificador."""

    with _conexion(ruta) as conexion:
        fila = conexion.execute(
            "SELECT * FROM escenarios WHERE id = ?", (escenario_id,)
        ).fetchone()
    return _fila_a_escenario(fila) if fila else None


def get_scenario_by_name(
    nombre: str, ruta: str | os.PathLike[str] | None = None
) -> dict | None:
    """Recupera un escenario por nombre, sin distinguir mayúsculas."""

    with _conexion(ruta) as conexion:
        fila = conexion.execute(
            "SELECT * FROM escenarios WHERE nombre_normalizado = ?",
            (_normalizar_nombre(nombre),),
        ).fetchone()
    return _fila_a_escenario(fila) if fila else None


def save_scenario(
    nombre: str,
    estados: Sequence[object],
    matriz: Sequence[Sequence[object]],
    distribucion_inicial: Sequence[object],
    ruta: str | os.PathLike[str] | None = None,
) -> dict:
    """Valida y guarda un escenario con nombre único."""

    if not isinstance(nombre, str) or not nombre.strip():
        raise ValidationError("El nombre del escenario no puede estar vacío.")
    nombre_limpio = nombre.strip()
    if len(nombre_limpio) > 80:
        raise ValidationError("El nombre del escenario no puede superar 80 caracteres.")

    estados_limpios = validate_states(estados)
    matriz_limpia = validate_matrix(matriz, len(estados_limpios))
    distribucion_limpia = validate_distribution(
        distribucion_inicial, len(estados_limpios)
    )

    try:
        with _conexion(ruta) as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO escenarios
                    (nombre, nombre_normalizado, estados, matriz, distribucion_inicial, creado_en)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    nombre_limpio,
                    _normalizar_nombre(nombre_limpio),
                    json.dumps(estados_limpios, ensure_ascii=False),
                    json.dumps(matriz_limpia),
                    json.dumps(distribucion_limpia),
                    _ahora(),
                ),
            )
            escenario_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        raise ScenarioExistsError("Ya existe un escenario con ese nombre.") from error

    escenario = get_scenario(escenario_id, ruta)
    if escenario is None:  # pragma: no cover - defensa ante fallos inesperados
        raise ValidationError("No se pudo recuperar el escenario guardado.")
    return escenario


def save_calculation(
    resultados: Sequence[dict],
    estacionaria: Sequence[float],
    escenario_id: int | None = None,
    ruta: str | os.PathLike[str] | None = None,
) -> int:
    """Registra un cálculo válido en el historial."""

    pasos = [int(resultado["paso"]) for resultado in resultados]
    with _conexion(ruta) as conexion:
        cursor = conexion.execute(
            """
            INSERT INTO calculos
                (escenario_id, pasos, resultados, estacionaria, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                escenario_id,
                json.dumps(pasos),
                json.dumps(resultados),
                json.dumps(list(estacionaria)),
                _ahora(),
            ),
        )
        return int(cursor.lastrowid)


def list_history(
    limite: int = 10, ruta: str | os.PathLike[str] | None = None
) -> list[dict]:
    """Devuelve los últimos cálculos registrados."""

    limite = max(1, min(int(limite), 50))
    with _conexion(ruta) as conexion:
        filas = conexion.execute(
            """
            SELECT c.*, e.nombre AS escenario_nombre
            FROM calculos c
            LEFT JOIN escenarios e ON e.id = c.escenario_id
            ORDER BY c.id DESC
            LIMIT ?
            """,
            (limite,),
        ).fetchall()

    historial = []
    for fila in filas:
        historial.append(
            {
                "id": fila["id"],
                "escenario_id": fila["escenario_id"],
                "escenario_nombre": fila["escenario_nombre"],
                "pasos": json.loads(fila["pasos"]),
                "resultados": json.loads(fila["resultados"]),
                "estacionaria": json.loads(fila["estacionaria"]),
                "creado_en": fila["creado_en"],
            }
        )
    return historial


def healthcheck(ruta: str | os.PathLike[str] | None = None) -> dict:
    """Comprueba que la base de datos responde y tiene las tablas esperadas."""

    with _conexion(ruta) as conexion:
        conexion.execute("SELECT 1").fetchone()
        escenarios = conexion.execute(
            "SELECT COUNT(*) AS total FROM escenarios"
        ).fetchone()["total"]
        calculos = conexion.execute(
            "SELECT COUNT(*) AS total FROM calculos"
        ).fetchone()["total"]
    return {"estado": "ok", "escenarios": escenarios, "calculos": calculos}
