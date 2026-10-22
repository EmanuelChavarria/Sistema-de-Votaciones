"""Endpoints de candidatos: registro, consulta y eliminación."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import DbSession, get_current_user
from app.schemas.candidate import CandidateCreate, CandidateRead
from app.schemas.common import ErrorResponse, Page, ValidationErrorResponse
from app.services import candidate_service

router = APIRouter(
    prefix="/candidates",
    tags=["Candidatos"],
    dependencies=[Depends(get_current_user)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Token ausente, inválido o expirado",
        }
    },
)


@router.post(
    "",
    response_model=CandidateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar candidato",
    description=(
        "Da de alta un candidato. El partido es opcional. No se puede registrar un "
        "candidato cuyo nombre coincida con el de un votante ya registrado."
    ),
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El nombre pertenece a un votante registrado",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Datos del candidato inválidos",
        },
    },
)
def create_candidate(payload: CandidateCreate, db: DbSession) -> CandidateRead:
    """Registra un candidato nuevo."""
    return candidate_service.create_candidate(db, payload)


@router.get(
    "",
    response_model=Page[CandidateRead],
    summary="Listar candidatos",
    description=(
        "Devuelve los candidatos registrados con filtros opcionales y paginación. "
        "El orden por defecto es por id ascendente."
    ),
)
def list_candidates(
    db: DbSession,
    party: str | None = Query(
        default=None, description="Filtra por partido (coincidencia exacta o parcial)"
    ),
    search: str | None = Query(
        default=None, description="Búsqueda parcial e insensible a mayúsculas sobre name"
    ),
    page: int = Query(default=1, ge=1, description="Número de página (base 1)"),
    page_size: int = Query(
        default=10, ge=1, le=100, description="Cantidad de elementos por página"
    ),
) -> Page[CandidateRead]:
    """Lista los candidatos con filtros y paginación."""
    return candidate_service.list_candidates(
        db, party=party, search=search, page=page, page_size=page_size
    )


@router.get(
    "/{candidate_id}",
    response_model=CandidateRead,
    summary="Obtener un candidato",
    description="Devuelve el candidato con el id indicado.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "El candidato no existe",
        }
    },
)
def get_candidate(candidate_id: int, db: DbSession) -> CandidateRead:
    """Devuelve el detalle de un candidato."""
    return candidate_service.get_candidate(db, candidate_id)


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un candidato",
    description=(
        "Elimina un candidato que todavía no tiene votos. Si tiene votos, se "
        "responde 409 porque esos votos forman parte de los resultados."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "El candidato no existe",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El candidato tiene votos registrados",
        },
    },
)
def delete_candidate(candidate_id: int, db: DbSession) -> Response:
    """Elimina un candidato sin votos registrados."""
    candidate_service.delete_candidate(db, candidate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
