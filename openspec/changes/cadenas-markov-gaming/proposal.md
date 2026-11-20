# Proposal

## Why

Predecir cómo evoluciona una sesión de videojuegos requiere calcular potencias de una matriz de transición, una tarea repetitiva y propensa a errores si se hace a mano. Una aplicación web que automatice el cálculo y lo explique visualmente permite demostrar el modelo de Markov, comparar escenarios y dejar evidencia reproducible del proceso.

## What Changes

- Se crea una aplicación web en Python con Flask que modela una sesión de gaming con tres estados: `Jugando`, `En pausa` y `Descansando`.
- El usuario puede editar la matriz de transición y la distribución inicial, y el sistema valida que sean probabilidades coherentes antes de calcular.
- Se calculan las probabilidades de cada estado para 1, 3, 5 y 10 pasos, además de pasos personalizados, usando `πₙ = π₀ · Pⁿ`.
- Se calcula y muestra la distribución estacionaria de la cadena.
- Los resultados se presentan en tablas y gráficas (líneas, barras, dona y mapa de calor de la matriz), con actualización dinámica y un fallback sin JavaScript.
- Se guardan escenarios e historial de cálculos en SQLite; la base de datos se inicializa y se siembra automáticamente.
- Se añade despliegue en Render con `render.yaml`, health check y documentación de la URL pública.
- Se documenta el flujo SDD con OpenSpec y se entrega una suite de pruebas automatizadas con pytest.
- **Fuera de alcance:** autenticación, multiusuario, edición colaborativa, migraciones de esquema, series temporales reales y despliegue con Postgres.

## Capabilities

### New Capabilities

- `prediccion-markov`: definición, validación, cálculo y visualización de una cadena de Markov para predecir estados futuros de una sesión de gaming, incluyendo distribución estacionaria y persistencia de escenarios e historial.

### Modified Capabilities

- Ninguna.

## Impact

- **Código nuevo:** `app/` con el motor matemático (`markov.py`), persistencia SQLite (`db.py`), aplicación Flask (`web.py`), plantillas Jinja y recursos estáticos; `wsgi.py` para Gunicorn; `scripts/build_docs.py` para la landing de GitHub Pages.
- **Dependencias:** Flask, Gunicorn y Chart.js (copiado al repositorio); pytest y pytest-cov para pruebas.
- **Datos:** archivo SQLite local `data/markov.db` con tablas `escenarios` y `calculos`; en Render el archivo es efímero y se reinicializa al arrancar.
- **Infraestructura:** `render.yaml` para desplegar el servicio web gratuito, `/api/salud` como health check y landing estática en GitHub Pages.
- **Riesgo principal:** que la validación numérica y el redondeo de la interfaz no coincidan con los valores esperados; se cubrirá con pruebas de referencia y tolerancias explícitas.
