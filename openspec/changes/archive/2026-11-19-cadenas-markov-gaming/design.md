# Design

## Context

Ver `proposal.md` para la motivación y `specs/prediccion-markov/spec.md` para los requisitos. El repositorio parte vacío: este cambio crea la aplicación completa. El dominio es una cadena de Markov de 3 a 6 estados que modela una sesión de gaming (`Jugando`, `En pausa`, `Descansando`), con matriz de transición editable, distribución inicial, cálculos a 1/3/5/10 pasos, pasos personalizados y distribución estacionaria.

Restricciones relevantes:

- La aplicación debe ser web y ejecutarse en Python con SQLite.
- Debe funcionar en local y en Render (plan gratuito, sistema de archivos efímero).
- La matemática debe ser determinista y verificable con valores de referencia.
- La interfaz debe funcionar con y sin JavaScript.
- El flujo SDD debe quedar evidenciado en `openspec/` y en el historial de Git.

## Goals / Non-Goals

**Goals:**

- Separar el motor matemático puro de la web y de la persistencia para poder probarlo de forma aislada.
- Fijar un contrato de validación único, reutilizado por la interfaz HTML, la API JSON y la base de datos.
- Ofrecer resultados numéricos exactos (tolerancia 1e-9) y una presentación con cuatro decimales.
- Persistir escenarios e historial sin exigir un servidor de base de datos.
- Desplegar en Render con un solo comando y un health check.

**Non-Goals:**

- Autenticación, multiusuario o control de acceso.
- Edición colaborativa en tiempo real.
- Migraciones de esquema (se usa `CREATE TABLE IF NOT EXISTS`).
- Persistencia garantizada en Render gratis (el disco es efímero).
- Series temporales reales o integración con APIs de videojuegos.

## Decisions

### 1. Motor matemático en Python puro

`app/markov.py` implementa:

- `validate_matrix(matriz, estados)` y `validate_distribution(pi, n)` con mensajes en español.
- `matmul`, `matpow` (exponenciación por cuadrados) y `distribution_after(pi, P, n)`.
- `compute_steps(pi, P, pasos)` para 1, 3, 5, 10 y pasos personalizados.
- `stationary_distribution(P)` resolviendo `(Pᵀ − I)π = 0` con la restricción `Σπ = 1` mediante eliminación gaussiana con pivoteo parcial.

Se evita NumPy para mantener las dependencias mínimas y porque las matrices son de tamaño 3–6. La exponenciación por cuadrados reduce el costo y evita errores de redondeo acumulados por multiplicaciones innecesarias.

**Alternativas consideradas:**

- NumPy: más rápido, pero añade una dependencia pesada para matrices diminutas.
- Iteración de potencias para la estacionaria: simple, pero puede no converger en cadenas periódicas; la resolución lineal es más robusta y verificable.

### 2. Flask con app factory y Gunicorn

`app/web.py` expone `create_app(config=None)`. La configuración acepta `DATABASE_PATH`, `SECRET_KEY` y `TESTING`. `wsgi.py` crea la instancia para Gunicorn (`wsgi:app`). En Render se usa un solo worker con hilos (`gthread`) para evitar bloqueos de SQLite; localmente basta `flask --app wsgi run --debug`.

Rutas:

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/` | Página principal con escenario por defecto y resultados |
| `POST` | `/calcular` | Cálculo con recarga completa (fallback sin JS) |
| `POST` | `/api/calcular` | Cálculo JSON usado por JavaScript |
| `GET` | `/api/escenarios` | Lista de escenarios guardados |
| `POST` | `/api/escenarios` | Guarda un escenario con nombre único |
| `GET` | `/api/escenarios/<id>` | Recupera un escenario |
| `GET` | `/api/historial` | Últimos cálculos registrados |
| `GET` | `/api/salud` | Health check de app y base de datos |

Los errores de validación devuelven 400 con `{"error": "..."}` en la API y un bloque de alerta en la interfaz; los recursos inexistentes devuelven 404.

### 3. SQLite con `sqlite3` de la biblioteca estándar

Esquema:

```sql
CREATE TABLE IF NOT EXISTS escenarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL UNIQUE,
  estados TEXT NOT NULL,
  matriz TEXT NOT NULL,
  distribucion_inicial TEXT NOT NULL,
  creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calculos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  escenario_id INTEGER REFERENCES escenarios(id),
  pasos TEXT NOT NULL,
  resultados TEXT NOT NULL,
  estacionaria TEXT NOT NULL,
  creado_en TEXT NOT NULL
);
```

- Los arreglos y matrices se guardan como JSON en columnas `TEXT`.
- `init_db()` crea las tablas y `seed_default_scenario()` inserta el escenario por defecto con `INSERT OR IGNORE`.
- Cada petición abre su propia conexión con `timeout=5`, `PRAGMA journal_mode=WAL` y `PRAGMA busy_timeout=5000`.
- En local la ruta por defecto es `data/markov.db`; en Render se configura con `DATABASE_PATH`.
- En Render gratis el archivo se pierde al reiniciar o redeployar; la app se reinicializa y siembra el escenario por defecto. Para persistencia se documenta un disco de pago o Render Postgres.

**Alternativas consideradas:**

- SQLAlchemy: útil si el esquema creciera, pero añade complejidad innecesaria para dos tablas.
- Postgres: descartado para la entrega porque exige credenciales y un servicio externo; se documenta como evolución.

### 4. Interfaz Jinja + JavaScript vanilla + Chart.js

- `index.html` renderiza la matriz y la distribución inicial como formularios; los resultados por defecto se calculan en el servidor para que la primera carga ya muestre datos.
- `app.js` intercepta el envío, llama a `/api/calcular`, actualiza la tabla y las gráficas sin recargar y muestra errores de validación.
- Sin JavaScript, el formulario hace `POST /calcular` y el servidor devuelve la misma plantilla con los resultados.
- Chart.js se copia a `app/static/vendor/` para no depender de un CDN en tiempo de ejecución.
- El mapa de calor se implementa con una cuadrícula HTML/CSS, sin plugins adicionales.

### 5. Estrategia de pruebas

- `tests/test_markov.py`: valores de referencia 1/3/5/10, potencias, suma de filas, estacionaria y propiedad `πP = π`.
- `tests/test_validation.py`: matriz no cuadrada, valores fuera de rango, filas que no suman 1, distribución inicial inválida y estados inválidos.
- `tests/test_db.py`: creación de tablas, seed idempotente, guardado/recuperación de escenarios e historial con una base temporal.
- `tests/test_api.py`: cálculo válido, errores 400, pasos personalizados, historial, CRUD de escenarios y health check.
- `tests/test_render.py`: la página responde 200, incluye las etiquetas de los estados, los canvas y los valores calculados.
- `tests/test_render_config.py`: `render.yaml` contiene el start command, el health check y `DATABASE_PATH`.
- `tests/test_e2e.py` (opcional, marcado `e2e`): flujo real con Playwright y Firefox.

Cobertura objetivo ≥ 85 % con `pytest --cov=app --cov-report=term-missing --cov-fail-under=85`. Las pruebas no dependen de red, hora ni aleatoriedad.

### 6. Render y GitHub Pages

- `render.yaml` define un servicio web `python`, plan `free`, `buildCommand` con `pip install -r requirements.txt`, `startCommand` con Gunicorn, health check en `/api/salud` y variables `PYTHON_VERSION`, `SECRET_KEY`, `APP_ENV` y `DATABASE_PATH`.
- `autoDeployTrigger: commit` para que cada push a `main` redeploye.
- `docs/index.html` es una landing estática generada por `scripts/build_docs.py` con el mismo motor Python: explicación del modelo, matriz, resultados, gráficas y enlace a la app de Render. Se publica desde `main` / `docs`.
- La app interactiva vive en Render; Pages solo aloja la landing porque no puede ejecutar Python.

### 7. Evidencia del proceso SDD

El cambio se desarrolla con el esquema `spec-driven` de OpenSpec: propuesta → especificación → diseño → tareas → implementación → archivo. Cada fase se valida con `openspec validate` y se registra en un commit independiente. Al final se archiva el cambio con `openspec archive` para promover la especificación a `openspec/specs/prediccion-markov/spec.md`.

## Risks / Trade-offs

- **Redondeo en la interfaz** → Los cálculos internos usan doble precisión y tolerancia 1e-9; la presentación redondea a cuatro decimales. Se prueba contra valores de referencia.
- **SQLite efímero en Render** → Aceptado y documentado para el plan gratuito; el seed garantiza que la app siempre arranque con datos utilizables.
- **Bloqueos de SQLite** → Un worker con hilos, WAL y `busy_timeout` reducen el riesgo; el volumen esperado es bajo.
- **Cadenas periódicas** → La estacionaria se obtiene resolviendo el sistema lineal, no por iteración, para evitar falsos no-convergentes.
- **Dependencia de Chart.js** → Se copia al repositorio y se versiona, evitando fallos por CDN.
- **Cold start de Render** → El plan gratuito tarda ~1 minuto tras 15 minutos de inactividad; se advierte en el README y en la landing.
