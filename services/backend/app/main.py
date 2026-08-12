from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.repositories.in_memory import (
    InMemoryMessageRepository,
    InMemoryUserRepository,
)
from app.routers import auth as auth_router
from app.routers import websocket as websocket_router
from app.services.auth import AuthService
from app.services.chat import ChatService, ConnectionManager
from app.services.translation.factory import create_translation_provider

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def create_app() -> FastAPI:
    app = FastAPI(title="chat-translation-backend", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router.router)
    app.include_router(websocket_router.router)
    user_repository = InMemoryUserRepository()
    app.state.user_repository = user_repository
    app.state.auth_service = AuthService(
        user_repository=user_repository,
    )
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
