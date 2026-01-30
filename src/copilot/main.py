"""Точка входа FastAPI приложения."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from copilot.config import get_settings
from copilot.routers import processing_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _validate_config() -> None:
    """Fail fast при старте, если конфиг невалиден."""
    get_settings()


app = FastAPI(
    title="Copilot API",
    description="API для транскрибации созвонов и ответов на вопросы",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(processing_router)


@app.on_event("startup")
async def startup() -> None:
    _validate_config()
    logger.info("Copilot API started")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
