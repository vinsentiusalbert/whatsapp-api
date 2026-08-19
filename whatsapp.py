"""Entry point ASGI yang stabil untuk Uvicorn dan wrapper WSGI cPanel."""

from wa_app.application import create_app


app = create_app()
