from fastapi import FastAPI

from app.repositories.in_memory import (
    InMemoryMessageRepository,
)
from app.routers import auth as auth_router
from app.routers import websocket as websocket_router
from app.services.chat import ChatService, ConnectionManager
from app.services.translation.factory import create_translation_provider


def create_app() -> FastAPI:
    app = FastAPI(title="chat-translation-backend", version="0.1.0")
    app.include_router(auth_router.router)
    app.include_router(websocket_router.router)
    app.state.chat_service = ChatService(
        manager=ConnectionManager(max_connections=10),
        translator=create_translation_provider(),
        repository=InMemoryMessageRepository(),
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
