# Tasks

## 1. Preparación del proyecto

- [x] 1.1 Crear la estructura `app/`, `app/templates/`, `app/static/`, `tests/`, `scripts/`, `data/` y `docs/` con sus archivos base; verificar con `find app tests scripts docs -type f` que existen los directorios y archivos esperados.
- [x] 1.2 Crear `requirements.txt` (Flask, Gunicorn), `requirements-dev.txt` (pytest, pytest-cov) y `.gitignore` (`.venv/`, `__pycache__/`, `*.db`, `.pytest_cache/`, `htmlcov/`, `.coverage`); verificar con `python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt` que la instalación termina sin errores.
- [x] 1.3 Crear `pytest.ini` con `testpaths = tests`, marcadores `e2e` y opciones de salida; verificar con `.venv/bin/pytest --collect-only -q` que descubre la suite sin fallar.

## 2. Motor matemático

- [x] 2.1 Implementar `app/markov.py` con `validate_matrix`, `validate_distribution`, `matmul`, `matpow` y `distribution_after`; verificar con pruebas unitarias de matrices conocidas y de errores de validación.
- [x] 2.2 Implementar `compute_steps` para 1, 3, 5 y 10 pasos más pasos personalizados ordenados y sin duplicados; verificar con los valores de referencia [0.7000, 0.2000, 0.1000], [0.5255, 0.2115, 0.2630], [0.4725, 0.2058, 0.3217] y [0.4477, 0.2029, 0.3494].
- [x] 2.3 Implementar `stationary_distribution` resolviendo `(Pᵀ − I)π = 0` con `Σπ = 1` mediante eliminación gaussiana con pivoteo; verificar que la matriz por defecto produce aproximadamente [0.4459, 0.2027, 0.3514] y que `πP = π` dentro de 1e-9.
- [x] 2.4 Definir el escenario por defecto (estados, matriz y distribución inicial) en un módulo de configuración reutilizable; verificar que las filas suman 1 y que la distribución inicial suma 1.

## 3. Persistencia SQLite

- [x] 3.1 Implementar `app/db.py` con conexión por petición, `init_db` y `seed_default_scenario` idempotente; verificar con una prueba que dos inicializaciones seguidas dejan exactamente un escenario por defecto.
- [x] 3.2 Implementar el guardado y la recuperación de escenarios con nombre único y validación de la matriz; verificar que un nombre duplicado se rechaza y que un escenario guardado se recupera por id y por nombre.
- [x] 3.3 Implementar el registro y listado del historial de cálculos (últimos 10, orden descendente); verificar que un cálculo válido queda registrado con su fecha y que un cálculo inválido no se registra.

## 4. Aplicación web

- [x] 4.1 Implementar `app/web.py` con `create_app`, la ruta `/`, `POST /calcular` y el filtro de formato a cuatro decimales; verificar con el cliente de pruebas que `/` responde 200 y contiene los tres estados.
- [x] 4.2 Implementar `POST /api/calcular` y `GET /api/salud`; verificar con pruebas de API que un cálculo válido devuelve 200 con resultados y estacionaria, y que los datos inválidos devuelven 400 sin guardar historial.
- [x] 4.3 Implementar `GET/POST /api/escenarios`, `GET /api/escenarios/<id>` y `GET /api/historial`; verificar con pruebas de API el alta, la consulta, el conflicto por nombre duplicado y el listado del historial.
- [x] 4.4 Crear `app/templates/base.html` e `index.html` con la matriz editable, la distribución inicial, la tabla de resultados, la sección de pasos detallados y los contenedores de las gráficas; verificar que el HTML incluye los canvas y la tabla con los valores calculados.
- [x] 4.5 Crear `app/static/css/styles.css` y `app/static/js/app.js` con la llamada a `/api/calcular`, la actualización de tablas y las gráficas de líneas, barras, dona y mapa de calor; verificar manualmente que al cambiar una celda y pulsar "Calcular" los resultados se actualizan sin recargar.
- [x] 4.6 Copiar Chart.js a `app/static/vendor/` y referenciarlo desde la plantilla; verificar que la página carga la gráfica sin acceso a Internet.

## 5. Pruebas e integración

- [x] 5.1 Escribir `tests/conftest.py` con una app de prueba y una base SQLite temporal por prueba; verificar que cada prueba parte de un estado limpio y que no se toca `data/markov.db`.
- [x] 5.2 Escribir `tests/test_markov.py` y `tests/test_validation.py` con al menos 20 casos; verificar con `.venv/bin/pytest tests/test_markov.py tests/test_validation.py -q` que todos pasan.
- [x] 5.3 Escribir `tests/test_db.py` y `tests/test_api.py` con al menos 15 casos; verificar con `.venv/bin/pytest tests/test_db.py tests/test_api.py -q` que todos pasan.
- [x] 5.4 Escribir `tests/test_render.py` y `tests/test_render_config.py`; verificar que la página contiene los estados, los canvas y los porcentajes, y que `render.yaml` declara start command, health check y `DATABASE_PATH`.
- [x] 5.5 Ejecutar la suite completa con cobertura y verificar que todas las pruebas pasan y que la cobertura es ≥ 85 %: `.venv/bin/pytest --cov=app --cov-report=term-missing --cov-fail-under=85`.

## 6. Documentación y despliegue

- [x] 6.1 Crear `wsgi.py` y `render.yaml` con el servicio web, Gunicorn, health check y variables de entorno; verificar con una prueba que el archivo contiene los valores esperados y con `gunicorn --check-config wsgi:app` que la configuración es válida.
- [x] 6.2 Crear `.github/workflows/tests.yml` para ejecutar pytest en Python 3.14 en cada push y pull request; verificar la sintaxis YAML con un parser y dejar documentado el comando local equivalente.
- [x] 6.3 Crear `scripts/build_docs.py` y `docs/index.html` con la landing estática (modelo, matriz, resultados, gráficas y enlace a Render); verificar que el script genera el HTML de forma determinista y que contiene los valores de referencia.
- [x] 6.4 Escribir `README.md` con descripción, modelo, matriz, fórmulas, instalación, ejecución local, pruebas, estructura, API, resultados, flujo OpenSpec/SDD, despliegue en Render, GitHub Pages y uso de IA; verificar que todos los comandos documentados se ejecutan tal cual.
- [x] 6.5 Capturar una imagen de la aplicación en ejecución con Firefox headless y guardarla en `docs/captura.png`; verificar que la imagen existe y que el README la referencia.

## 7. Verificación final

- [x] 7.1 Ejecutar `.venv/bin/pytest -q` y `.venv/bin/pytest --cov=app --cov-report=term-missing --cov-fail-under=85`; verificar que no hay fallos ni pruebas omitidas inesperadas.
- [x] 7.2 Ejecutar `openspec validate --all --strict`; verificar que no hay errores ni advertencias.
- [x] 7.3 Arrancar la app con Gunicorn, ejecutar el flujo crear escenario → calcular → consultar historial y verificar que `/api/salud` responde 200 y que los resultados coinciden con la tabla de referencia.
- [x] 7.4 Verificar el historial de Git con `git log --oneline --graph` y que el repositorio remoto contiene `main`, la rama de trabajo y el tag `v1.0.0`.

## Workflow follow-up

- Revisar el cambio completo contra la especificación y la propuesta antes de archivar.
- Archivar el cambio con `openspec archive cadenas-markov-gaming -y` y verificar que `openspec/specs/prediccion-markov/spec.md` contiene los requisitos promovidos.
- Tras el despliegue en Render, actualizar la URL pública en el README y en `docs/index.html`, y verificar que responde 200.
