from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Role, User
from app.routers import auth
from app.security import hash_password


def init_db() -> None:
    """Create tables and the first admin account (if no admin exists yet)."""
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.role == Role.admin)) is None:
            db.add(
                User(
                    email=settings.admin_email.lower(),
                    full_name="Administrator",
                    password_hash=hash_password(settings.admin_password),
                    role=Role.admin,
                )
            )
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="DocVerify AI API",
    version="0.2.0",
    description="Backend for DocVerify AI: accounts, roles, documents, review and administration.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/api/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": "backend"}
