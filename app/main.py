"""Punto de entrada de la API de Sistema de Votaciones."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.routers import auth, candidates, voters, votes
from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.schemas.common import HealthResponse
from app.services.auth_service import ensure_admin_user

settings = get_settings()

OPENAPI_TAGS = [
    {
        "name": "Auth",
        "description": "Registro de usuarios e inicio de sesión con tokens JWT.",
    },
    {
        "name": "Votantes",
        "description": "Registro, consulta, filtrado y eliminación de votantes.",
    },
    {
        "name": "Candidatos",
        "description": "Registro, consulta, filtrado y eliminación de candidatos.",
    },
    {
        "name": "Votos",
        "description": "Emisión de votos (un voto por votante) y estadísticas de resultados.",
    },
    {
        "name": "Sistema",
        "description": "Endpoints de información y estado del servicio.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Prepara la base de datos: crea las tablas y el usuario administrador inicial."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_admin_user(
            db, settings.FIRST_ADMIN_USERNAME, settings.FIRST_ADMIN_PASSWORD
        )
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
    """Traduce las excepciones de dominio al formato de error unificado."""
    headers = dict(exc.headers)
    if exc.status_code == 401:
        headers.setdefault("WWW-Authenticate", "Bearer")
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=headers
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    """Red de seguridad para violaciones de integridad no controladas (carreras)."""
    return JSONResponse(
        status_code=409,
        content={
            "detail": "La operación entra en conflicto con datos que ya existen."
        },
    )


app.include_router(auth.router)
app.include_router(voters.router)
app.include_router(candidates.router)
app.include_router(votes.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Sistema"],
    summary="Estado del servicio",
    description="Endpoint público que confirma que la API está operativa.",
)
def health() -> HealthResponse:
    """Devuelve el estado del servicio."""
    return HealthResponse(status="ok")
