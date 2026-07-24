import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, github, query
from app.core.config import settings
from app.db.database import init_db
from app.services.github_sync import poll_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # CREATE EXTENSION vector + create_all — fine for a hackathon

    poll_task = None
    if settings.github_sync_enabled:
        poll_task = asyncio.create_task(poll_loop())

    yield

    if poll_task:
        poll_task.cancel()


app = FastAPI(
    title="NexusMind API",
    description="Role-based engineering knowledge graph & onboarding assistant.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(auth.router)
app.include_router(github.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
