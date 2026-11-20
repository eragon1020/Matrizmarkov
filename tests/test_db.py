"""Pruebas de persistencia SQLite."""

from __future__ import annotations

import sqlite3

import pytest

from app.config import (
    DISTRIBUCION_POR_DEFECTO,
    ESTADOS_POR_DEFECTO,
    MATRIZ_POR_DEFECTO,
    NOMBRE_ESCENARIO_POR_DEFECTO,
)
from app.db import (
    ScenarioExistsError,
    ensure_database,
    get_scenario,
    get_scenario_by_name,
    healthcheck,
    init_db,
    list_history,
    list_scenarios,
    save_calculation,
    save_scenario,
)
from app.markov import ValidationError, default_scenario


def test_init_db_crea_las_tablas(db_path):
    init_db(db_path)
    with sqlite3.connect(db_path) as conexion:
        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"escenarios", "calculos"} <= tablas


def test_ensure_database_siembra_un_solo_escenario(db_path):
    ensure_database(db_path)
    ensure_database(db_path)
    escenarios = list_scenarios(db_path)
    assert len(escenarios) == 1
    assert escenarios[0]["nombre"] == NOMBRE_ESCENARIO_POR_DEFECTO
    assert escenarios[0]["estados"] == ESTADOS_POR_DEFECTO
    for fila_obtenida, fila_esperada in zip(
        escenarios[0]["matriz"], MATRIZ_POR_DEFECTO
    ):
        assert fila_obtenida == pytest.approx(fila_esperada)
    assert escenarios[0]["distribucion_inicial"] == pytest.approx(
        DISTRIBUCION_POR_DEFECTO
    )


def test_guardar_y_recuperar_escenario(db_path):
    ensure_database(db_path)
    escenario = save_scenario(
        "Mi sesión",
        ESTADOS_POR_DEFECTO,
        MATRIZ_POR_DEFECTO,
        DISTRIBUCION_POR_DEFECTO,
        db_path,
    )
    assert escenario["id"] > 0
    assert get_scenario(escenario["id"], db_path)["nombre"] == "Mi sesión"
    assert (
        get_scenario_by_name("mi SESIÓN", db_path)["id"] == escenario["id"]
    )


def test_nombre_duplicado_sin_importar_mayusculas(db_path):
    ensure_database(db_path)
    save_scenario(
        "Sesión única",
        ESTADOS_POR_DEFECTO,
        MATRIZ_POR_DEFECTO,
        DISTRIBUCION_POR_DEFECTO,
        db_path,
    )
    with pytest.raises(ScenarioExistsError, match="Ya existe"):
        save_scenario(
            "sesión ÚNICA",
            ESTADOS_POR_DEFECTO,
            MATRIZ_POR_DEFECTO,
            DISTRIBUCION_POR_DEFECTO,
            db_path,
        )


def test_nombre_vacio_se_rechaza(db_path):
    ensure_database(db_path)
    with pytest.raises(ValidationError, match="nombre"):
        save_scenario(
            "   ",
            ESTADOS_POR_DEFECTO,
            MATRIZ_POR_DEFECTO,
            DISTRIBUCION_POR_DEFECTO,
            db_path,
        )


def test_nombre_demasiado_largo_se_rechaza(db_path):
    ensure_database(db_path)
    with pytest.raises(ValidationError, match="80"):
        save_scenario(
            "x" * 81,
            ESTADOS_POR_DEFECTO,
            MATRIZ_POR_DEFECTO,
            DISTRIBUCION_POR_DEFECTO,
            db_path,
        )


def test_escenario_con_matriz_invalida_se_rechaza(db_path):
    ensure_database(db_path)
    with pytest.raises(ValidationError, match="sumar 1"):
        save_scenario(
            "Inválido",
            ESTADOS_POR_DEFECTO,
            [[0.5, 0.2, 0.1], [0.4, 0.3, 0.3], [0.15, 0.15, 0.70]],
            DISTRIBUCION_POR_DEFECTO,
            db_path,
        )


def test_listar_escenarios_incluye_el_por_defecto(db_path):
    ensure_database(db_path)
    save_scenario(
        "Otro",
        ESTADOS_POR_DEFECTO,
        MATRIZ_POR_DEFECTO,
        DISTRIBUCION_POR_DEFECTO,
        db_path,
    )
    nombres = [escenario["nombre"] for escenario in list_scenarios(db_path)]
    assert NOMBRE_ESCENARIO_POR_DEFECTO in nombres
    assert "Otro" in nombres


def test_escenario_inexistente_devuelve_none(db_path):
    ensure_database(db_path)
    assert get_scenario(999, db_path) is None
    assert get_scenario_by_name("No existe", db_path) is None


def test_guardar_y_listar_historial(db_path):
    ensure_database(db_path)
    resultado = default_scenario()
    calculo_id = save_calculation(
        resultado["resultados"],
        resultado["estacionaria"],
        escenario_id=1,
        ruta=db_path,
    )
    historial = list_history(10, db_path)
    assert len(historial) == 1
    assert historial[0]["id"] == calculo_id
    assert historial[0]["escenario_id"] == 1
    assert historial[0]["escenario_nombre"] == NOMBRE_ESCENARIO_POR_DEFECTO
    assert historial[0]["pasos"] == [1, 3, 5, 10]
    assert historial[0]["estacionaria"] == pytest.approx(
        resultado["estacionaria"]
    )
    assert historial[0]["creado_en"]


def test_historial_sin_escenario(db_path):
    ensure_database(db_path)
    resultado = default_scenario()
    save_calculation(resultado["resultados"], resultado["estacionaria"], None, db_path)
    historial = list_history(10, db_path)
    assert historial[0]["escenario_id"] is None
    assert historial[0]["escenario_nombre"] is None


def test_historial_ordenado_y_limitado(db_path):
    ensure_database(db_path)
    resultado = default_scenario()
    ids = [
        save_calculation(
            resultado["resultados"], resultado["estacionaria"], None, db_path
        )
        for _ in range(3)
    ]
    historial = list_history(2, db_path)
    assert [item["id"] for item in historial] == [ids[2], ids[1]]


def test_healthcheck(db_path):
    ensure_database(db_path)
    estado = healthcheck(db_path)
    assert estado["estado"] == "ok"
    assert estado["escenarios"] == 1
    assert estado["calculos"] == 0
