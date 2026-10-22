"""Endpoints de votos: emisión y estadísticas de resultados."""

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, get_current_user
from app.schemas.common import ErrorResponse, Page, ValidationErrorResponse
from app.schemas.vote import VoteCreate, VoteRead, VoteStatistics
from app.services import vote_service

router = APIRouter(
    prefix="/votes",
    tags=["Votos"],
    dependencies=[Depends(get_current_user)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Token ausente, inválido o expirado",
        }
    },
)


# Importante: esta ruta se declara antes que cualquier ruta con parámetro de path
# para que "statistics" nunca se interprete como un {id}.
@router.get(
    "/statistics",
    response_model=VoteStatistics,
    summary="Ver estadísticas de la votación",
    description=(
        "Devuelve el total de votos, los votantes registrados, los votantes que ya "
        "votaron, el porcentaje de participación y el resultado por candidato "
        "(incluidos los que tienen cero votos), ordenado por votos descendente."
    ),
)
def get_statistics(db: DbSession) -> VoteStatistics:
    """Calcula las estadísticas de la votación."""
    return vote_service.get_statistics(db)


@router.post(
    "",
    response_model=VoteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir un voto",
    description=(
        "Registra el voto de un votante a favor de un candidato. La operación es "
        "atómica: marca al votante como `has_voted` e incrementa los votos del "
        "candidato en la misma transacción. Un votante solo puede votar una vez."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "El votante o el candidato no existen",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El votante ya ha emitido su voto",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Datos del voto inválidos",
        },
    },
)
def create_vote(payload: VoteCreate, db: DbSession) -> VoteRead:
    """Emite un voto de forma atómica."""
    return vote_service.cast_vote(db, payload)


@router.get(
    "",
    response_model=Page[VoteRead],
    summary="Listar votos",
    description="Devuelve los votos emitidos con paginación, ordenados por id ascendente.",
)
def list_votes(
    db: DbSession,
    page: int = Query(default=1, ge=1, description="Número de página (base 1)"),
    page_size: int = Query(
        default=10, ge=1, le=100, description="Cantidad de elementos por página"
    ),
) -> Page[VoteRead]:
    """Lista los votos emitidos."""
    return vote_service.list_votes(db, page=page, page_size=page_size)
