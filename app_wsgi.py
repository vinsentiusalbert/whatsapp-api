"""WSGI entry point untuk cPanel Phusion Passenger.

Nama file sengaja bukan ``passenger_wsgi.py`` karena cPanel dapat membuat dan
menimpa file tersebut sebagai wrapper internal.
"""

from a2wsgi import ASGIMiddleware

from whatsapp import app


application = ASGIMiddleware(app)
