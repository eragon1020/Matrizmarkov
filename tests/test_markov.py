"""Pruebas del motor matemático de cadenas de Markov."""

from __future__ import annotations

import pytest

from app.config import (
    DISTRIBUCION_POR_DEFECTO,
    ESTADOS_POR_DEFECTO,
    MATRIZ_POR_DEFECTO,
    PASOS_REQUERIDOS,
)
from app.markov import (
    compute_all,
    default_scenario,
    distribution_after,
    format_probability,
    matmul,
    matpow,
    parse_steps,
    stationary_distribution,
)

REFERENCIA = {
    1: [0.7000, 0.2000, 0.1000],
    3: [0.5255, 0.2115, 0.2630],
    5: [0.4725, 0.2058, 0.3217],
    10: [0.4477, 0.2029, 0.3494],
}

ESTACIONARIA = [0.4459459459, 0.2027027027, 0.3513513514]


def _aprox_matriz(obtenida, esperada):
    assert len(obtenida) == len(esperada)
    for fila_obtenida, fila_esperada in zip(obtenida, esperada):
        assert fila_obtenida == pytest.approx(fila_esperada, abs=1e-9)


def test_escenario_por_defecto_tiene_tres_estados():
    resultado = default_scenario()
    assert resultado["estados"] == ESTADOS_POR_DEFECTO
    assert len(resultado["matriz"]) == 3
    assert len(resultado["distribucion_inicial"]) == 3


def test_filas_de_la_matriz_por_defecto_suman_uno():
    for fila in MATRIZ_POR_DEFECTO:
        assert sum(fila) == pytest.approx(1.0, abs=1e-12)


def test_distribucion_inicial_suma_uno():
    assert sum(DISTRIBUCION_POR_DEFECTO) == pytest.approx(1.0, abs=1e-12)


def test_pasos_requeridos_son_1_3_5_10():
    assert PASOS_REQUERIDOS == (1, 3, 5, 10)


def test_resultados_de_referencia():
    resultado = compute_all(
        ESTADOS_POR_DEFECTO, MATRIZ_POR_DEFECTO, DISTRIBUCION_POR_DEFECTO
    )
    calculados = {
        fila["paso"]: fila["probabilidades"] for fila in resultado["resultados"]
    }
    assert set(calculados) == {1, 3, 5, 10}
    for paso, esperado in REFERENCIA.items():
        assert calculados[paso] == pytest.approx(esperado, abs=1e-4)


def test_cada_distribucion_calculada_suma_uno():
    resultado = compute_all(
        ESTADOS_POR_DEFECTO, MATRIZ_POR_DEFECTO, DISTRIBUCION_POR_DEFECTO
    )
    for fila in resultado["resultados"]:
        assert sum(fila["probabilidades"]) == pytest.approx(1.0, abs=1e-9)


def test_matmul_con_valores_conocidos():
    a = [[1.0, 2.0], [3.0, 4.0]]
    b = [[5.0, 6.0], [7.0, 8.0]]
    assert matmul(a, b) == [[19.0, 22.0], [43.0, 50.0]]


def test_matpow_cero_devuelve_identidad():
    assert matpow(MATRIZ_POR_DEFECTO, 0) == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def test_matpow_uno_devuelve_la_matriz():
    _aprox_matriz(matpow(MATRIZ_POR_DEFECTO, 1), MATRIZ_POR_DEFECTO)


def test_matpow_dos_coincide_con_multiplicacion_manual():
    _aprox_matriz(
        matpow(MATRIZ_POR_DEFECTO, 2),
        matmul(MATRIZ_POR_DEFECTO, MATRIZ_POR_DEFECTO),
    )


def test_matpow_conserva_la_suma_de_filas():
    for paso in (1, 3, 5, 10, 25):
        potencia = matpow(MATRIZ_POR_DEFECTO, paso)
        for fila in potencia:
            assert sum(fila) == pytest.approx(1.0, abs=1e-9)


def test_distribution_after_coincide_con_matpow():
    esperado = matmul(
        [DISTRIBUCION_POR_DEFECTO], matpow(MATRIZ_POR_DEFECTO, 5)
    )[0]
    assert distribution_after(
        DISTRIBUCION_POR_DEFECTO, MATRIZ_POR_DEFECTO, 5
    ) == pytest.approx(esperado)


def test_estacionaria_por_defecto():
    estacionaria = stationary_distribution(MATRIZ_POR_DEFECTO)
    assert estacionaria == pytest.approx(ESTACIONARIA, abs=1e-8)
    assert sum(estacionaria) == pytest.approx(1.0, abs=1e-9)


def test_estacionaria_cumple_pi_p_igual_pi():
    estacionaria = stationary_distribution(MATRIZ_POR_DEFECTO)
    verificacion = matmul([estacionaria], MATRIZ_POR_DEFECTO)[0]
    assert verificacion == pytest.approx(estacionaria, abs=1e-9)


def test_estacionaria_es_unica_y_no_negativa():
    estacionaria = stationary_distribution(MATRIZ_POR_DEFECTO)
    assert all(valor >= 0.0 for valor in estacionaria)
    assert len(estacionaria) == 3


def test_cadena_de_cuatro_estados(payload_4):
    resultado = compute_all(
        payload_4["estados"],
        payload_4["matriz"],
        payload_4["distribucion_inicial"],
    )
    assert len(resultado["estados"]) == 4
    assert len(resultado["estacionaria"]) == 4
    assert sum(resultado["estacionaria"]) == pytest.approx(1.0, abs=1e-9)
    verificacion = matmul([resultado["estacionaria"]], payload_4["matriz"])[0]
    assert verificacion == pytest.approx(resultado["estacionaria"], abs=1e-9)


def test_pasos_personalizados_se_ordenan_y_deduplican():
    resultado = compute_all(
        ESTADOS_POR_DEFECTO,
        MATRIZ_POR_DEFECTO,
        DISTRIBUCION_POR_DEFECTO,
        "10, 2, 7, 2, 3",
    )
    pasos = [fila["paso"] for fila in resultado["resultados"]]
    assert pasos == [1, 2, 3, 5, 7, 10]
    assert resultado["pasos_personalizados"] == [2, 7]


def test_pasos_personalizados_marcados():
    resultado = compute_all(
        ESTADOS_POR_DEFECTO,
        MATRIZ_POR_DEFECTO,
        DISTRIBUCION_POR_DEFECTO,
        [2, 7],
    )
    personalizados = {
        fila["paso"] for fila in resultado["resultados"] if fila["personalizado"]
    }
    assert personalizados == {2, 7}


def test_parse_steps_acepta_varios_formatos():
    assert parse_steps(None) == []
    assert parse_steps("") == []
    assert parse_steps("2, 7") == [2, 7]
    assert parse_steps("2;7") == [2, 7]
    assert parse_steps([7, 2, 2]) == [2, 7]
    assert parse_steps([2.0, 7.0]) == [2, 7]
    assert parse_steps(5) == [5]


@pytest.mark.parametrize("valor", [0, -1, 1.5, "abc", True, "2,", [2, "x"]])
def test_parse_steps_rechaza_valores_invalidos(valor):
    with pytest.raises(ValueError):
        parse_steps(valor)


def test_format_probability():
    assert format_probability(0.7) == "0.7000"
    assert format_probability(0.447678) == "0.4477"
    assert format_probability(0.0) == "0.0000"
