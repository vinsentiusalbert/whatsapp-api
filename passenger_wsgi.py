"""Entry point untuk cPanel Setup Python App (Phusion Passenger/WSGI)."""

from a2wsgi import ASGIMiddleware

from whatsapp import app


# Passenger mencari callable WSGI bernama `application`.
application = ASGIMiddleware(app)

