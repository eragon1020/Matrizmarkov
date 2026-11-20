"""Punto de entrada para Gunicorn y para el servidor de desarrollo de Flask."""

from app.web import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
