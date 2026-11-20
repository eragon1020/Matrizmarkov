"""Configuración y escenario por defecto de la cadena de Markov."""

ESTADOS_POR_DEFECTO = ["Jugando", "En pausa", "Descansando"]

MATRIZ_POR_DEFECTO = [
    [0.70, 0.20, 0.10],
    [0.40, 0.30, 0.30],
    [0.15, 0.15, 0.70],
]

DISTRIBUCION_POR_DEFECTO = [1.0, 0.0, 0.0]

PASOS_REQUERIDOS = (1, 3, 5, 10)

NOMBRE_ESCENARIO_POR_DEFECTO = "Sesión de gaming (por defecto)"

DESCRIPCION_ESTADOS = {
    "Jugando": "El jugador está en una partida activa.",
    "En pausa": "El jugador está en menús, tienda o chat.",
    "Descansando": "El jugador está fuera del juego.",
}
