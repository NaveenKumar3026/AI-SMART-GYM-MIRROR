from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, auth, sessions, ws as ws_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="AI Smart Gym Mirror - Backend")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(ws_router.router, prefix="/api/v1")

    return app


app = create_app()


@app.on_event("startup")
async def on_startup():
    # place for startup tasks (connect to redis, preload models, etc.)
    pass


@app.on_event("shutdown")
async def on_shutdown():
    # place for cleanup
    pass
