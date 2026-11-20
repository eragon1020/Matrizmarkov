"""Pruebas de configuración de despliegue y de la landing estática."""

from __future__ import annotations

from pathlib import Path

from app.markov import default_scenario
from scripts.build_docs import construir_html

RAIZ = Path(__file__).resolve().parent.parent


def test_render_yaml_declara_el_servicio():
    contenido = (RAIZ / "render.yaml").read_text(encoding="utf-8")
    assert "runtime: python" in contenido
    assert "plan: free" in contenido
    assert "healthCheckPath: /api/salud" in contenido
    assert "wsgi:app" in contenido
    assert "DATABASE_PATH" in contenido
    assert "PYTHON_VERSION" in contenido
    assert "SECRET_KEY" in contenido


def test_wsgi_expone_la_aplicacion():
    contenido = (RAIZ / "wsgi.py").read_text(encoding="utf-8")
    assert "create_app" in contenido
    assert "app = create_app()" in contenido


def test_requirements_incluye_gunicorn():
    contenido = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    assert "Flask" in contenido
    assert "gunicorn" in contenido


def test_workflow_de_pruebas():
    contenido = (RAIZ / ".github" / "workflows" / "tests.yml").read_text(
        encoding="utf-8"
    )
    assert "pytest" in contenido
    assert 'python-version: "3.14"' in contenido
    assert "--cov-fail-under=85" in contenido


def test_gitignore_excluye_entorno_y_bases():
    contenido = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert ".venv/" in contenido
    assert "*.db" in contenido
    assert "__pycache__/" in contenido


def test_landing_es_deterministica():
    resultado = default_scenario()
    primera = construir_html(resultado)
    segunda = construir_html(resultado)
    assert primera == segunda
    assert "Jugando" in primera
    assert "0.4477" in primera
    assert "0.4459" in primera
    assert "chart.umd.min.js" in primera
    assert "render.com" in primera


def test_landing_generada_existe():
    index = RAIZ / "docs" / "index.html"
    assert index.exists()
    contenido = index.read_text(encoding="utf-8")
    assert "Cadenas de Markov" in contenido
    assert "0.4477" in contenido
    assert (RAIZ / "docs" / "chart.umd.min.js").exists()
    assert (RAIZ / "docs" / ".nojekyll").exists()
