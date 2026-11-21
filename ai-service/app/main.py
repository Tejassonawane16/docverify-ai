"""DocVerify AI - AI service.

Phase 2: placeholder service so the architecture and containers are in place.
Phase 3: OCR/PDF parsing, document classification, field extraction and RAG verification.
"""

from functools import lru_cache

from fastapi import FastAPI
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = "ollama"
    llm_model: str = "llama3.1:8b"
    qdrant_url: str = "http://qdrant:6333"
    confidence_threshold: int = 70
    top_k: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()


app = FastAPI(title="DocVerify AI - AI Service", version="0.2.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ai-service"}


@app.get("/config")
def config() -> dict:
    """Current AI configuration (US-18). No secrets are returned."""
    return get_settings().model_dump()


@app.post("/verify", status_code=501)
def verify() -> dict:
    return {"detail": "AI verification is implemented in Phase 3"}
