"""Pruebas de la interfaz HTTP y de la API JSON."""

from __future__ import annotations

import pytest

ESTACIONARIA = [0.4459459459, 0.2027027027, 0.3513513514]


def test_home_responde_200(client):
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert b"Jugando" in respuesta.data
    assert b"grafico-lineas" in respuesta.data
    assert b"0.4477" in respuesta.data


def test_calcular_formulario_valido(client, payload, form_data):
    respuesta = client.post("/calcular", data=form_data(payload))
    assert respuesta.status_code == 200
    assert b"0.4477" in respuesta.data
    assert b"Paso 10" in respuesta.data


def test_calcular_formulario_invalido(client, payload, form_data):
    datos = form_data(payload)
    datos["m_0_1"] = "0.00"
    respuesta = client.post("/calcular", data=datos)
    assert respuesta.status_code == 400
    assert b"debe sumar 1" in respuesta.data


def test_api_calcular_valido(client, payload):
    respuesta = client.post("/api/calcular", json=payload)
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["ok"] is True
    resultado = datos["resultado"]
    assert resultado["estados"] == payload["estados"]
    assert resultado["estacionaria"] == pytest.approx(ESTACIONARIA, abs=1e-8)
    assert [fila["paso"] for fila in resultado["resultados"]] == [1, 3, 5, 10]


def test_api_calcular_invalido_no_guarda_historial(client, payload):
    matriz = [fila[:] for fila in payload["matriz"]]
    matriz[0][1] = 0.0
    respuesta = client.post(
        "/api/calcular",
        json={**payload, "matriz": matriz},
    )
    assert respuesta.status_code == 400
    assert respuesta.get_json()["ok"] is False
    assert client.get("/api/historial").get_json()["historial"] == []


def test_api_calcular_sin_json(client):
    respuesta = client.post(
        "/api/calcular", data="esto no es json", content_type="text/plain"
    )
    assert respuesta.status_code == 400
    assert "JSON" in respuesta.get_json()["error"]


def test_api_calcular_campos_faltantes(client):
    respuesta = client.post("/api/calcular", json={})
    assert respuesta.status_code == 400
    assert respuesta.get_json()["ok"] is False


def test_api_calcular_pasos_personalizados(client, payload):
    respuesta = client.post(
        "/api/calcular", json={**payload, "pasos_personalizados": "2, 7"}
    )
    assert respuesta.status_code == 200
    pasos = [fila["paso"] for fila in respuesta.get_json()["resultado"]["resultados"]]
    assert pasos == [1, 2, 3, 5, 7, 10]


def test_api_historial_registra_calculo(client, payload):
    client.post("/api/calcular", json=payload)
    respuesta = client.get("/api/historial")
    assert respuesta.status_code == 200
    historial = respuesta.get_json()["historial"]
    assert len(historial) == 1
    assert historial[0]["pasos"] == [1, 3, 5, 10]
    assert historial[0]["estacionaria"] == pytest.approx(ESTACIONARIA, abs=1e-8)


def test_api_historial_limite_invalido(client):
    respuesta = client.get("/api/historial?limite=abc")
    assert respuesta.status_code == 400


def test_api_escenarios_crud(client, payload):
    alta = client.post(
        "/api/escenarios",
        json={"nombre": "Escenario de prueba", **payload},
    )
    assert alta.status_code == 201
    escenario = alta.get_json()["escenario"]
    assert escenario["id"] > 0
    assert escenario["nombre"] == "Escenario de prueba"

    listado = client.get("/api/escenarios")
    assert listado.status_code == 200
    assert any(
        item["id"] == escenario["id"]
        for item in listado.get_json()["escenarios"]
    )

    detalle = client.get(f"/api/escenarios/{escenario['id']}")
    assert detalle.status_code == 200
    assert detalle.get_json()["escenario"]["nombre"] == "Escenario de prueba"

    duplicado = client.post(
        "/api/escenarios",
        json={"nombre": "ESCENARIO DE PRUEBA", **payload},
    )
    assert duplicado.status_code == 409

    invalido = client.post(
        "/api/escenarios",
        json={
            "nombre": "Inválido",
            "estados": payload["estados"],
            "matriz": [[0.5, 0.2, 0.1], [0.4, 0.3, 0.3], [0.15, 0.15, 0.70]],
            "distribucion_inicial": payload["distribucion_inicial"],
        },
    )
    assert invalido.status_code == 400

    inexistente = client.get("/api/escenarios/999")
    assert inexistente.status_code == 404


def test_api_escenario_sin_nombre(client, payload):
    respuesta = client.post(
        "/api/escenarios",
        json={"nombre": "", **payload},
    )
    assert respuesta.status_code == 400


def test_api_salud(client):
    respuesta = client.get("/api/salud")
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["estado"] == "ok"
    assert datos["app"] == "1.0.0"
    assert datos["base_de_datos"]["estado"] == "ok"
    assert datos["base_de_datos"]["escenarios"] == 1


def test_home_con_escenario_guardado(client, payload):
    alta = client.post(
        "/api/escenarios", json={"nombre": "Cargado", **payload}
    ).get_json()["escenario"]
    respuesta = client.get(f"/?escenario={alta['id']}")
    assert respuesta.status_code == 200
    assert b"Jugando" in respuesta.data


def test_calcular_asocia_historial_al_escenario(client, payload, form_data):
    datos = form_data(payload, escenario_id="1")
    respuesta = client.post("/calcular", data=datos)
    assert respuesta.status_code == 200
    historial = client.get("/api/historial").get_json()["historial"]
    assert historial[0]["escenario_id"] == 1


def test_formulario_de_cuatro_estados(client, payload_4, form_data):
    respuesta = client.post("/calcular", data=form_data(payload_4))
    assert respuesta.status_code == 200
    assert b"Socializando" in respuesta.data


def test_api_cuatro_estados(client, payload_4):
    respuesta = client.post("/api/calcular", json=payload_4)
    assert respuesta.status_code == 200
    resultado = respuesta.get_json()["resultado"]
    assert len(resultado["estados"]) == 4
    assert len(resultado["estacionaria"]) == 4
    assert sum(resultado["estacionaria"]) == pytest.approx(1.0, abs=1e-9)
