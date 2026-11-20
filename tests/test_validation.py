"""Pruebas de validación de matrices, distribuciones y estados."""

from __future__ import annotations

import math

import pytest

from app.markov import (
    ValidationError,
    compute_all,
    distribution_after,
    matmul,
    matpow,
    stationary_distribution,
    validate_distribution,
    validate_matrix,
    validate_states,
)

MATRIZ_VALIDA = [
    [0.70, 0.20, 0.10],
    [0.40, 0.30, 0.30],
    [0.15, 0.15, 0.70],
]


def test_estados_validos_se_normalizan():
    assert validate_states(["  Jugando ", "En pausa", "Descansando"]) == [
        "Jugando",
        "En pausa",
        "Descansando",
    ]


def test_estados_deben_ser_lista():
    with pytest.raises(ValidationError, match="lista"):
        validate_states("Jugando,En pausa,Descansando")


def test_estados_minimo_tres():
    with pytest.raises(ValidationError, match="entre 3 y 6"):
        validate_states(["A", "B"])


def test_estados_maximo_seis():
    with pytest.raises(ValidationError, match="entre 3 y 6"):
        validate_states([f"E{i}" for i in range(7)])


def test_estados_no_pueden_estar_vacios():
    with pytest.raises(ValidationError, match="nombre no vacío"):
        validate_states(["A", "   ", "C"])


def test_estados_no_pueden_repetirse_sin_importar_mayusculas():
    with pytest.raises(ValidationError, match="únicos"):
        validate_states(["Jugando", "jugando", "Descansando"])


def test_estados_deben_ser_texto():
    with pytest.raises(ValidationError, match="nombre no vacío"):
        validate_states(["A", 2, "C"])


def test_matriz_valida_se_devuelve_como_flotantes():
    matriz = validate_matrix(MATRIZ_VALIDA, 3)
    assert isinstance(matriz[0][0], float)
    for fila_obtenida, fila_esperada in zip(matriz, MATRIZ_VALIDA):
        assert fila_obtenida == pytest.approx(fila_esperada)


def test_matriz_debe_ser_lista():
    with pytest.raises(ValidationError, match="lista de filas"):
        validate_matrix("0.7,0.2,0.1", 3)


def test_matriz_no_puede_estar_vacia():
    with pytest.raises(ValidationError, match="vacía"):
        validate_matrix([], 3)


def test_matriz_debe_ser_cuadrada():
    with pytest.raises(ValidationError, match="cuadrada"):
        validate_matrix([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]], 3)


def test_matriz_debe_coincidir_con_el_numero_de_estados():
    with pytest.raises(ValidationError, match="4 filas"):
        validate_matrix(MATRIZ_VALIDA, 4)


def test_matriz_respeta_minimo_de_filas():
    with pytest.raises(ValidationError, match="entre 3 y 6"):
        validate_matrix([[0.5, 0.5], [0.5, 0.5]])


def test_matriz_respeta_maximo_de_filas():
    matriz = [[1.0 if i == j else 0.0 for j in range(7)] for i in range(7)]
    with pytest.raises(ValidationError, match="entre 3 y 6"):
        validate_matrix(matriz)


def test_fila_debe_ser_lista():
    with pytest.raises(ValidationError, match="fila 1"):
        validate_matrix([0.5, 0.25, 0.25], 3)


def test_probabilidad_negativa():
    matriz = [[-0.10, 0.50, 0.60], [0.40, 0.30, 0.30], [0.15, 0.15, 0.70]]
    with pytest.raises(ValidationError, match="entre 0 y 1"):
        validate_matrix(matriz, 3)


def test_probabilidad_mayor_que_uno():
    matriz = [[1.10, -0.05, -0.05], [0.40, 0.30, 0.30], [0.15, 0.15, 0.70]]
    with pytest.raises(ValidationError, match="entre 0 y 1"):
        validate_matrix(matriz, 3)


def test_fila_que_no_suma_uno():
    matriz = [[0.50, 0.20, 0.10], [0.40, 0.30, 0.30], [0.15, 0.15, 0.70]]
    with pytest.raises(ValidationError, match="debe sumar 1"):
        validate_matrix(matriz, 3)


def test_valor_no_numerico():
    matriz = [["a", 0.20, 0.80], [0.40, 0.30, 0.30], [0.15, 0.15, 0.70]]
    with pytest.raises(ValidationError, match="número"):
        validate_matrix(matriz, 3)


def test_valor_booleano_no_es_numero():
    matriz = [[True, 0.0, 0.0], [0.40, 0.30, 0.30], [0.15, 0.15, 0.70]]
    with pytest.raises(ValidationError, match="número"):
        validate_matrix(matriz, 3)


@pytest.mark.parametrize("valor", [math.nan, math.inf, -math.inf])
def test_valor_no_finito(valor):
    matriz = [[valor, 0.20, 0.80], [0.40, 0.30, 0.30], [0.15, 0.15, 0.70]]
    with pytest.raises(ValidationError, match="finito"):
        validate_matrix(matriz, 3)


def test_distribucion_valida():
    assert validate_distribution([0.2, 0.3, 0.5], 3) == [0.2, 0.3, 0.5]


def test_distribucion_longitud_incorrecta():
    with pytest.raises(ValidationError, match="3 valores"):
        validate_distribution([0.5, 0.5], 3)


def test_distribucion_no_es_lista():
    with pytest.raises(ValidationError, match="lista"):
        validate_distribution("1,0,0", 3)


def test_distribucion_negativa():
    with pytest.raises(ValidationError, match="entre 0 y 1"):
        validate_distribution([-0.1, 0.6, 0.5], 3)


def test_distribucion_mayor_que_uno():
    with pytest.raises(ValidationError, match="entre 0 y 1"):
        validate_distribution([1.1, -0.05, -0.05], 3)


def test_distribucion_no_suma_uno():
    with pytest.raises(ValidationError, match="sumar 1"):
        validate_distribution([0.2, 0.2, 0.2], 3)


def test_distribucion_no_numerica():
    with pytest.raises(ValidationError, match="número"):
        validate_distribution(["a", 0.5, 0.5], 3)


def test_distribucion_no_finita():
    with pytest.raises(ValidationError, match="finito"):
        validate_distribution([math.nan, 0.5, 0.5], 3)


def test_matmul_dimensiones_incompatibles():
    with pytest.raises(ValidationError, match="dimensiones"):
        matmul([[1.0, 2.0]], [[1.0, 2.0]])


def test_matmul_matrices_vacias():
    with pytest.raises(ValidationError, match="vacías"):
        matmul([], [])


@pytest.mark.parametrize("exponente", [-1, 1.5, True])
def test_matpow_rechaza_exponentes_invalidos(exponente):
    with pytest.raises(ValidationError, match="entero no negativo"):
        matpow(MATRIZ_VALIDA, exponente)


def test_matpow_rechaza_matriz_no_cuadrada():
    with pytest.raises(ValidationError, match="cuadrada"):
        matpow([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]], 2)


def test_distribution_after_dimensiones_incompatibles():
    with pytest.raises(ValidationError, match="misma dimensión"):
        distribution_after([1.0, 0.0], MATRIZ_VALIDA, 1)


def test_estacionaria_rechaza_matriz_no_cuadrada():
    with pytest.raises(ValidationError, match="cuadrada"):
        stationary_distribution([[0.5, 0.5]])


def test_compute_all_rechaza_matriz_invalida():
    with pytest.raises(ValidationError, match="debe sumar 1"):
        compute_all(
            ["A", "B", "C"],
            [[0.5, 0.2, 0.1], [0.4, 0.3, 0.3], [0.15, 0.15, 0.70]],
            [1.0, 0.0, 0.0],
        )
