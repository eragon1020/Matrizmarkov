"""Pruebas de la página HTML y de los recursos estáticos."""

from __future__ import annotations


def test_pagina_incluye_estados_y_componentes(client):
    respuesta = client.get("/")
    html = respuesta.data

    assert respuesta.status_code == 200
    for texto in (b"Jugando", b"En pausa", b"Descansando"):
        assert texto in html
    for identificador in (
        b'id="grafico-lineas"',
        b'id="grafico-barras"',
        b'id="grafico-dona"',
        b'id="mapa-calor"',
        b'id="tabla-resultados"',
        b'id="paso-a-paso"',
    ):
        assert identificador in html


def test_pagina_incluye_valores_calculados(client):
    html = client.get("/").data
    assert b"0.7000" in html
    assert b"0.4477" in html
    assert b"0.4459" in html


def test_pagina_incluye_datos_para_javascript(client):
    html = client.get("/").data
    assert b'type="application/json" id="datos-resultado"' in html
    assert b"chart.umd.min.js" in html
    assert b"js/app.js" in html


def test_pagina_muestra_error_de_validacion(client, payload, form_data):
    datos = form_data(payload)
    datos["m_0_1"] = "0.00"
    respuesta = client.post("/calcular", data=datos)
    assert respuesta.status_code == 400
    assert b'class="alert"' in respuesta.data
    assert b"debe sumar 1" in respuesta.data


def test_pagina_muestra_pasos_personalizados(client, payload, form_data):
    datos = form_data(payload, pasos_personalizados="7")
    respuesta = client.post("/calcular", data=datos)
    assert respuesta.status_code == 200
    assert b"Paso 7" in respuesta.data


def test_pagina_muestra_historial_tras_calcular(client, payload):
    client.post("/api/calcular", json=payload)
    html = client.get("/").data
    assert b"Historial reciente" in html
    assert b"C\xc3\xa1lculo libre" in html or b"libre" in html


def test_recursos_estaticos(client):
    assert client.get("/static/css/styles.css").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200
    assert client.get("/static/vendor/chart.umd.min.js").status_code == 200


def test_pagina_de_cuatro_estados(client, payload_4, form_data):
    respuesta = client.post("/calcular", data=form_data(payload_4))
    assert respuesta.status_code == 200
    assert b"Socializando" in respuesta.data
    assert b"0.2500" in respuesta.data
