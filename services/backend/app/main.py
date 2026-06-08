from fastapi import FastAPI

from app.core.config import get_settings
from app.routers import auth as auth_router
from app.routers import websocket as websocket_router


def create_app() -> FastAPI:
    _ = get_settings()
    app = FastAPI(title="chat-translation-backend", version="0.1.0")
    app.include_router(auth_router.router)
    app.include_router(websocket_router.router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
