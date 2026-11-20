# Spec Delta

## Purpose

Predecir la evolución de una sesión de gaming mediante una cadena de Markov, validando la matriz de transición y presentando las probabilidades futuras y la distribución estacionaria de forma comprensible y reproducible.

## ADDED Requirements

### Requirement: Definición de la cadena de Markov

El sistema MUST permitir configurar una cadena de Markov con entre 3 y 6 estados, cada uno con un nombre no vacío y único, una matriz de transición cuadrada y una distribución inicial. La matriz define la probabilidad de pasar del estado de la fila al estado de la columna.

#### Scenario: Configurar una cadena de tres estados

- **WHEN** se envían tres estados llamados "Jugando", "En pausa" y "Descansando" junto con una matriz de 3x3 y una distribución inicial de tres valores
- **THEN** el sistema acepta la configuración y la deja disponible para el cálculo

#### Scenario: Rechazar menos de tres estados

- **WHEN** se intenta configurar una cadena con dos estados
- **THEN** el sistema rechaza la configuración con un mensaje en español y no calcula resultados

#### Scenario: Rechazar nombres vacíos o repetidos

- **WHEN** se configura una cadena con un nombre de estado vacío o con dos estados con el mismo nombre
- **THEN** el sistema rechaza la configuración con un mensaje en español y no calcula resultados

### Requirement: Validación de la matriz de transición

El sistema MUST validar que la matriz sea cuadrada, que cada probabilidad esté entre 0 y 1 y que cada fila sume 1 con una tolerancia de 1e-9. Si alguna condición falla, MUST rechazar el cálculo con un mensaje en español y MUST NOT guardar resultados.

#### Scenario: Aceptar una matriz válida

- **WHEN** se envía una matriz cuadrada con valores entre 0 y 1 cuyas filas suman 1
- **THEN** el sistema acepta la matriz y continúa con el cálculo

#### Scenario: Rechazar una probabilidad fuera de rango

- **WHEN** se envía una matriz con un valor negativo o mayor que 1
- **THEN** el sistema rechaza el cálculo con un mensaje en español y no guarda resultados

#### Scenario: Rechazar una fila que no suma 1

- **WHEN** se envía una matriz cuya fila suma 0.8 o 1.2
- **THEN** el sistema rechaza el cálculo con un mensaje en español y no guarda resultados

#### Scenario: Rechazar una matriz no cuadrada

- **WHEN** se envía una matriz con un número de columnas distinto al número de estados
- **THEN** el sistema rechaza el cálculo con un mensaje en español y no guarda resultados

### Requirement: Validación de la distribución inicial

El sistema MUST validar que la distribución inicial tenga un valor por estado, que cada valor esté entre 0 y 1 y que la suma sea 1 con una tolerancia de 1e-9. Si no cumple, MUST rechazar el cálculo con un mensaje en español.

#### Scenario: Aceptar una distribución inicial válida

- **WHEN** se envía una distribución inicial con un valor por estado, todos entre 0 y 1, que suman 1
- **THEN** el sistema acepta la distribución y continúa con el cálculo

#### Scenario: Rechazar una longitud incorrecta

- **WHEN** se envía una distribución inicial con menos o más valores que estados tiene la cadena
- **THEN** el sistema rechaza el cálculo con un mensaje en español

#### Scenario: Rechazar una suma incorrecta

- **WHEN** se envía una distribución inicial cuyos valores suman 0.9 o 1.1
- **THEN** el sistema rechaza el cálculo con un mensaje en español

### Requirement: Cálculo de probabilidades en pasos requeridos

El sistema MUST calcular la distribución de probabilidad en los pasos 1, 3, 5 y 10 aplicando `πₙ = π₀ · Pⁿ`, y MUST mostrar cada probabilidad con cuatro decimales. La suma de cada distribución calculada MUST ser 1 con una tolerancia de 1e-9.

#### Scenario: Calcular los resultados de referencia

- **WHEN** se usa la matriz por defecto y la distribución inicial [1, 0, 0]
- **THEN** el paso 1 devuelve [0.7000, 0.2000, 0.1000], el paso 3 devuelve [0.5255, 0.2115, 0.2630], el paso 5 devuelve [0.4725, 0.2058, 0.3217] y el paso 10 devuelve [0.4477, 0.2029, 0.3494]

#### Scenario: Conservar la suma de probabilidades

- **WHEN** se calcula cualquier paso de una cadena válida
- **THEN** la suma de las probabilidades de todos los estados es 1 con una tolerancia de 1e-9

### Requirement: Pasos personalizados

El sistema MUST aceptar pasos adicionales enteros positivos, calcular sus distribuciones y presentarlos ordenados y sin duplicados junto con los pasos requeridos. MUST rechazar pasos no enteros, cero o negativos con un mensaje en español.

#### Scenario: Agregar pasos personalizados

- **WHEN** se solicitan los pasos 7 y 2 además de los pasos requeridos
- **THEN** el sistema calcula las distribuciones de 2 y 7 y las presenta ordenadas junto con 1, 3, 5 y 10, sin repetir pasos

#### Scenario: Rechazar un paso inválido

- **WHEN** se solicita un paso igual a 0, negativo o con decimales
- **THEN** el sistema rechaza la solicitud con un mensaje en español y no calcula resultados

### Requirement: Distribución estacionaria

El sistema MUST calcular y mostrar una distribución estacionaria `π` que cumpla `πP = π`, con todos sus valores entre 0 y 1 y suma 1 con una tolerancia de 1e-9. Para la matriz por defecto MUST mostrar aproximadamente 0.4459, 0.2027 y 0.3514.

#### Scenario: Calcular la estacionaria de la matriz por defecto

- **WHEN** se calcula la distribución estacionaria de la matriz por defecto
- **THEN** el sistema devuelve aproximadamente [0.4459, 0.2027, 0.3514] y la suma es 1

#### Scenario: Verificar la propiedad de estacionariedad

- **WHEN** se multiplica la distribución estacionaria calculada por la matriz de transición
- **THEN** el resultado coincide con la misma distribución dentro de una tolerancia de 1e-9

### Requirement: Visualización de resultados

El sistema MUST presentar los resultados en una tabla numérica y en gráficas de líneas, barras y dona, además de un mapa de calor de la matriz. Con JavaScript disponible MUST actualizar los resultados sin recargar la página; sin JavaScript MUST seguir funcionando mediante un envío de formulario.

#### Scenario: Mostrar las gráficas y la tabla

- **WHEN** se calculan los resultados de una cadena válida
- **THEN** la página muestra la tabla de probabilidades por paso, la gráfica de líneas, la gráfica de barras, la dona de la distribución estacionaria y el mapa de calor de la matriz

#### Scenario: Actualizar sin recargar la página

- **WHEN** el usuario modifica la matriz y pulsa "Calcular" con JavaScript habilitado
- **THEN** los resultados y las gráficas se actualizan en la misma página sin recargarla

#### Scenario: Funcionar sin JavaScript

- **WHEN** el usuario envía el formulario con JavaScript deshabilitado
- **THEN** el servidor procesa los datos y devuelve la página con los resultados calculados

### Requirement: Persistencia de escenarios e historial

El sistema MUST guardar escenarios con nombre único y el historial de cálculos en SQLite. Al arrancar MUST crear las tablas si no existen y MUST sembrar un escenario por defecto de forma idempotente. MUST exponer los escenarios y los últimos cálculos mediante la interfaz y la API.

#### Scenario: Inicializar la base de datos

- **WHEN** la aplicación arranca con una base de datos vacía
- **THEN** crea las tablas necesarias y deja disponible exactamente un escenario por defecto sin duplicarlo en arranques posteriores

#### Scenario: Guardar y recuperar un escenario

- **WHEN** el usuario guarda un escenario con un nombre nuevo y una matriz válida
- **THEN** el escenario queda almacenado y puede recuperarse después por su identificador o por su nombre

#### Scenario: Registrar el historial de cálculos

- **WHEN** se realiza un cálculo válido
- **THEN** el sistema registra el cálculo con su fecha y lo muestra entre los últimos cálculos realizados

### Requirement: Interfaz web y manejo de errores

El sistema MUST servir la aplicación en la ruta raíz con código 200 y MUST exponer un health check que verifique la aplicación y la base de datos. Ante datos inválidos MUST responder con código 400 y un mensaje en español, sin guardar el cálculo.

#### Scenario: Cargar la aplicación

- **WHEN** un usuario visita la ruta raíz
- **THEN** el sistema responde con código 200 y muestra el escenario por defecto con sus estados, matriz y resultados iniciales

#### Scenario: Informar un error de validación

- **WHEN** se envían datos inválidos al cálculo
- **THEN** el sistema responde con código 400, muestra un mensaje en español y no registra el cálculo en el historial

#### Scenario: Verificar la salud del servicio

- **WHEN** se consulta el health check
- **THEN** el sistema responde con código 200 y confirma que la aplicación y la base de datos están operativas
