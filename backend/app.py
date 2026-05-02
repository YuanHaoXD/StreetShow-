from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import ASSET_DIR, CORS_ALLOW_ORIGINS, validate_config
from .core.logging import setup_logging
from .core.model import DEVICE
from .routers import advanced, advanced_async, multi, process


def create_app() -> FastAPI:
    setup_logging()
    validate_config()
    app = FastAPI(title="StreetShow Backend", version="0.5.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS.split(","),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/assets", StaticFiles(directory=str(ASSET_DIR)), name="assets")
    app.include_router(process.router)
    app.include_router(advanced.router)
    app.include_router(advanced_async.router)
    app.include_router(multi.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "device": DEVICE}

    return app
