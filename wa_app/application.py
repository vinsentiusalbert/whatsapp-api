from contextlib import asynccontextmanager

from fastapi import FastAPI

from wa_app.database import ensure_tables
from wa_app.routers import messages, myads, status, webhook

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        ensure_tables()
    except Exception as error:
        print("WARNING ensure_tables:", str(error))
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="MyWhatsApp + MyAds Campaign Bot", version="2.0.0", lifespan=lifespan)
    # Endpoint tanpa business logic diletakkan di router status yang stabil.
    app.include_router(status.router)
    app.include_router(messages.router)
    app.include_router(myads.router)
    app.include_router(webhook.router)
    return app
