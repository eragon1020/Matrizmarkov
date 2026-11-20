"""Fixtures compartidas por la suite de pruebas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.web import create_app  # noqa: E402


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "markov-test.db"


@pytest.fixture
def app(db_path: Path):
    aplicacion = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "clave-de-prueba",
            "DATABASE_PATH": str(db_path),
        }
    )
    return aplicacion


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def payload() -> dict:
    return {
        "estados": ["Jugando", "En pausa", "Descansando"],
        "matriz": [
            [0.70, 0.20, 0.10],
            [0.40, 0.30, 0.30],
            [0.15, 0.15, 0.70],
        ],
        "distribucion_inicial": [1.0, 0.0, 0.0],
    }


@pytest.fixture
def payload_4() -> dict:
    return {
        "estados": ["Jugando", "En pausa", "Descansando", "Socializando"],
        "matriz": [
            [0.50, 0.20, 0.20, 0.10],
            [0.20, 0.50, 0.20, 0.10],
            [0.10, 0.20, 0.60, 0.10],
            [0.25, 0.25, 0.25, 0.25],
        ],
        "distribucion_inicial": [0.25, 0.25, 0.25, 0.25],
    }


def formulario_desde_payload(payload: dict, **overrides) -> dict:
    """Convierte un payload JSON en datos de formulario HTML."""

    n = len(payload["estados"])
    datos = {"n_estados": str(n), "pasos_personalizados": ""}
    for i, estado in enumerate(payload["estados"]):
        datos[f"e_{i}"] = estado
    for i, fila in enumerate(payload["matriz"]):
        for j, valor in enumerate(fila):
            datos[f"m_{i}_{j}"] = str(valor)
    for i, valor in enumerate(payload["distribucion_inicial"]):
        datos[f"p_{i}"] = str(valor)
    datos.update(overrides)
    return datos


@pytest.fixture
def form_data():
    return formulario_desde_payload
