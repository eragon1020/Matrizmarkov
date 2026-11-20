"""Motor matemático de cadenas de Markov.

El módulo es independiente de Flask y de SQLite para poder probarlo de forma
aislada. Todas las funciones reciben y devuelven estructuras de Python simples.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

from .config import (
    DISTRIBUCION_POR_DEFECTO,
    ESTADOS_POR_DEFECTO,
    MATRIZ_POR_DEFECTO,
    PASOS_REQUERIDOS,
)

EPS = 1e-9
MIN_ESTADOS = 3
MAX_ESTADOS = 6


class ValidationError(ValueError):
    """Error de validación con un mensaje pensado para mostrarse al usuario."""


def _es_numero(valor: object) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _a_flotante(valor: object, contexto: str) -> float:
    if not _es_numero(valor):
        raise ValidationError(f"{contexto} debe ser un número.")
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValidationError(f"{contexto} debe ser un número finito.")
    return numero


def validate_states(estados: Sequence[object]) -> list[str]:
    """Valida y normaliza los nombres de los estados."""

    if isinstance(estados, (str, bytes)) or not isinstance(estados, (list, tuple)):
        raise ValidationError("Los estados deben enviarse como una lista.")
    if not MIN_ESTADOS <= len(estados) <= MAX_ESTADOS:
        raise ValidationError(
            f"La cadena debe tener entre {MIN_ESTADOS} y {MAX_ESTADOS} estados."
        )

    limpios: list[str] = []
    for indice, estado in enumerate(estados, start=1):
        if not isinstance(estado, str) or not estado.strip():
            raise ValidationError(f"El estado {indice} debe tener un nombre no vacío.")
        limpios.append(estado.strip())

    normalizados = [estado.casefold() for estado in limpios]
    if len(set(normalizados)) != len(normalizados):
        raise ValidationError("Los nombres de los estados deben ser únicos.")

    return limpios


def validate_matrix(
    matriz: Sequence[Sequence[object]], n_estados: int | None = None
) -> list[list[float]]:
    """Valida una matriz de transición y la devuelve como flotantes."""

    if isinstance(matriz, (str, bytes)) or not isinstance(matriz, (list, tuple)):
        raise ValidationError("La matriz debe enviarse como una lista de filas.")
    if not matriz:
        raise ValidationError("La matriz no puede estar vacía.")

    filas = len(matriz)
    if n_estados is not None and filas != n_estados:
        raise ValidationError(
            f"La matriz debe tener {n_estados} filas, pero tiene {filas}."
        )
    if filas < MIN_ESTADOS or filas > MAX_ESTADOS:
        raise ValidationError(
            f"La matriz debe tener entre {MIN_ESTADOS} y {MAX_ESTADOS} filas."
        )

    resultado: list[list[float]] = []
    for i, fila in enumerate(matriz, start=1):
        if isinstance(fila, (str, bytes)) or not isinstance(fila, (list, tuple)):
            raise ValidationError(f"La fila {i} debe ser una lista de números.")
        if len(fila) != filas:
            raise ValidationError(
                f"La matriz debe ser cuadrada: la fila {i} tiene {len(fila)} valores "
                f"y se esperaban {filas}."
            )

        valores = [
            _a_flotante(valor, f"La probabilidad de la fila {i}, columna {j}")
            for j, valor in enumerate(fila, start=1)
        ]
        for j, valor in enumerate(valores, start=1):
            if valor < 0.0 or valor > 1.0:
                raise ValidationError(
                    f"La probabilidad de la fila {i}, columna {j} debe estar entre 0 y 1."
                )
        if abs(sum(valores) - 1.0) > EPS:
            raise ValidationError(
                f"La fila {i} debe sumar 1 (suma actual: {sum(valores):.6f})."
            )
        resultado.append(valores)

    return resultado


def validate_distribution(
    distribucion: Sequence[object], n_estados: int
) -> list[float]:
    """Valida una distribución de probabilidad de longitud ``n_estados``."""

    if isinstance(distribucion, (str, bytes)) or not isinstance(
        distribucion, (list, tuple)
    ):
        raise ValidationError("La distribución inicial debe ser una lista de números.")
    if len(distribucion) != n_estados:
        raise ValidationError(
            f"La distribución inicial debe tener {n_estados} valores, "
            f"pero tiene {len(distribucion)}."
        )

    valores = [
        _a_flotante(valor, f"La probabilidad inicial del estado {i}")
        for i, valor in enumerate(distribucion, start=1)
    ]
    for i, valor in enumerate(valores, start=1):
        if valor < 0.0 or valor > 1.0:
            raise ValidationError(
                f"La probabilidad inicial del estado {i} debe estar entre 0 y 1."
            )
    if abs(sum(valores) - 1.0) > EPS:
        raise ValidationError(
            f"La distribución inicial debe sumar 1 (suma actual: {sum(valores):.6f})."
        )
    return valores


def matmul(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> list[list[float]]:
    """Multiplica dos matrices."""

    if len(a) == 0 or len(b) == 0:
        raise ValidationError("No se pueden multiplicar matrices vacías.")
    if len(a[0]) != len(b):
        raise ValidationError("Las dimensiones de las matrices no son compatibles.")

    filas = len(a)
    columnas = len(b[0])
    resultado = [[0.0] * columnas for _ in range(filas)]
    for i in range(filas):
        for k in range(len(b)):
            aik = a[i][k]
            if aik == 0.0:
                continue
            for j in range(columnas):
                resultado[i][j] += aik * b[k][j]
    return resultado


def matpow(matriz: Sequence[Sequence[float]], exponente: int) -> list[list[float]]:
    """Eleva una matriz a un exponente entero no negativo."""

    if not isinstance(exponente, int) or isinstance(exponente, bool) or exponente < 0:
        raise ValidationError("El número de pasos debe ser un entero no negativo.")

    n = len(matriz)
    if n == 0 or any(len(fila) != n for fila in matriz):
        raise ValidationError("La matriz debe ser cuadrada.")

    resultado = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    base = [list(map(float, fila)) for fila in matriz]
    exponente_restante = exponente
    while exponente_restante > 0:
        if exponente_restante & 1:
            resultado = matmul(resultado, base)
        exponente_restante >>= 1
        if exponente_restante:
            base = matmul(base, base)
    return resultado


def distribution_after(
    distribucion: Sequence[float],
    matriz: Sequence[Sequence[float]],
    pasos: int,
) -> list[float]:
    """Calcula ``π₀ · Pⁿ`` para un número de pasos."""

    if len(distribucion) != len(matriz):
        raise ValidationError(
            "La distribución inicial y la matriz deben tener la misma dimensión."
        )
    potencia = matpow(matriz, pasos)
    return matmul([list(map(float, distribucion))], potencia)[0]


def parse_steps(valor: object) -> list[int]:
    """Convierte una entrada de pasos personalizados en enteros positivos."""

    if valor is None:
        return []
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return []
        partes = [parte.strip() for parte in texto.replace(";", ",").split(",")]
        if any(not parte for parte in partes):
            raise ValidationError("Los pasos personalizados deben ser enteros positivos.")
        crudos: Iterable[object] = partes
    elif isinstance(valor, (list, tuple)):
        crudos = valor
    else:
        crudos = [valor]

    pasos: list[int] = []
    for crudo in crudos:
        if isinstance(crudo, bool):
            raise ValidationError("Los pasos personalizados deben ser enteros positivos.")
        if isinstance(crudo, int):
            numero = crudo
        elif isinstance(crudo, float):
            if not crudo.is_integer():
                raise ValidationError(
                    "Los pasos personalizados deben ser enteros positivos."
                )
            numero = int(crudo)
        elif isinstance(crudo, str) and crudo.strip().lstrip("+-").isdigit():
            numero = int(crudo.strip())
        else:
            raise ValidationError("Los pasos personalizados deben ser enteros positivos.")
        if numero <= 0:
            raise ValidationError("Los pasos personalizados deben ser mayores que cero.")
        pasos.append(numero)

    return sorted(set(pasos))


def _resolver_sistema(a: Sequence[Sequence[float]], b: Sequence[float]) -> list[float]:
    """Resuelve un sistema lineal con eliminación de Gauss-Jordan."""

    n = len(a)
    matriz = [list(map(float, a[i])) + [float(b[i])] for i in range(n)]

    for columna in range(n):
        pivote = max(range(columna, n), key=lambda fila: abs(matriz[fila][columna]))
        if abs(matriz[pivote][columna]) < 1e-12:
            raise ValidationError(
                "No se pudo calcular una distribución estacionaria única para esta matriz."
            )
        matriz[columna], matriz[pivote] = matriz[pivote], matriz[columna]

        valor_pivote = matriz[columna][columna]
        for j in range(columna, n + 1):
            matriz[columna][j] /= valor_pivote

        for fila in range(n):
            if fila == columna:
                continue
            factor = matriz[fila][columna]
            if factor == 0.0:
                continue
            for j in range(columna, n + 1):
                matriz[fila][j] -= factor * matriz[columna][j]

    return [matriz[i][n] for i in range(n)]


def stationary_distribution(matriz: Sequence[Sequence[float]]) -> list[float]:
    """Calcula la distribución estacionaria resolviendo ``πP = π`` y ``Σπ = 1``."""

    n = len(matriz)
    if n == 0 or any(len(fila) != n for fila in matriz):
        raise ValidationError("La matriz debe ser cuadrada.")

    # (Pᵀ − I)π = 0; se reemplaza la última ecuación por Σπ = 1.
    a = [
        [float(matriz[j][i]) - (1.0 if i == j else 0.0) for j in range(n)]
        for i in range(n)
    ]
    b = [0.0] * n
    a[-1] = [1.0] * n
    b[-1] = 1.0

    solucion = _resolver_sistema(a, b)
    solucion = [0.0 if abs(valor) < 1e-12 else valor for valor in solucion]

    if any(valor < -1e-7 for valor in solucion):
        raise ValidationError(
            "La distribución estacionaria calculada contiene valores negativos."
        )

    solucion = [max(0.0, valor) for valor in solucion]
    suma = sum(solucion)
    if suma <= 0.0:
        raise ValidationError("No se pudo normalizar la distribución estacionaria.")
    solucion = [valor / suma for valor in solucion]

    verificacion = matmul([solucion], [list(map(float, fila)) for fila in matriz])[0]
    if max(abs(verificacion[i] - solucion[i]) for i in range(n)) > 1e-6:
        raise ValidationError("La distribución calculada no es estacionaria.")

    return solucion


def compute_all(
    estados: Sequence[object],
    matriz: Sequence[Sequence[object]],
    distribucion_inicial: Sequence[object],
    pasos_personalizados: object = None,
) -> dict:
    """Valida la cadena y calcula pasos requeridos, personalizados y estacionaria."""

    estados_limpios = validate_states(estados)
    matriz_limpia = validate_matrix(matriz, len(estados_limpios))
    distribucion_limpia = validate_distribution(
        distribucion_inicial, len(estados_limpios)
    )
    personalizados = [
        paso for paso in parse_steps(pasos_personalizados) if paso not in PASOS_REQUERIDOS
    ]

    pasos = sorted(set(PASOS_REQUERIDOS).union(personalizados))
    resultados = []
    for paso in pasos:
        resultados.append(
            {
                "paso": paso,
                "probabilidades": distribution_after(
                    distribucion_limpia, matriz_limpia, paso
                ),
                "matriz": matpow(matriz_limpia, paso),
                "personalizado": paso not in PASOS_REQUERIDOS,
            }
        )

    return {
        "estados": estados_limpios,
        "matriz": matriz_limpia,
        "distribucion_inicial": distribucion_limpia,
        "pasos_requeridos": list(PASOS_REQUERIDOS),
        "pasos_personalizados": personalizados,
        "resultados": resultados,
        "estacionaria": stationary_distribution(matriz_limpia),
    }


def default_scenario() -> dict:
    """Devuelve el escenario por defecto ya calculado."""

    return compute_all(
        ESTADOS_POR_DEFECTO,
        MATRIZ_POR_DEFECTO,
        DISTRIBUCION_POR_DEFECTO,
    )


def format_probability(valor: float) -> str:
    """Formatea una probabilidad con cuatro decimales."""

    return f"{valor:.4f}"
