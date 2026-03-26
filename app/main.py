"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app import models  # noqa: F401 — register models with metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CAIT API",
    description="Capacity-Aware Intelligent Task Allocation System",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}
