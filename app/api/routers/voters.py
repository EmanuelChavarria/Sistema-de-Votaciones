"""Endpoints de votantes: registro, consulta y eliminación."""

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import DbSession, get_current_user
from app.schemas.common import ErrorResponse, Page, ValidationErrorResponse
from app.schemas.voter import VoterCreate, VoterRead
from app.services import voter_service

router = APIRouter(
    prefix="/voters",
    tags=["Votantes"],
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
    response_model=VoterRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar votante",
    description=(
        "Da de alta un votante. El email es único y se guarda en minúsculas. "
        "No se puede registrar un votante cuyo nombre coincida con el de un "
        "candidato ya registrado."
    ),
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Email duplicado o el nombre pertenece a un candidato",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Datos del votante inválidos",
        },
    },
)
def create_voter(payload: VoterCreate, db: DbSession) -> VoterRead:
    """Registra un votante nuevo."""
    return voter_service.create_voter(db, payload)


@router.get(
    "",
    response_model=Page[VoterRead],
    summary="Listar votantes",
    description=(
        "Devuelve los votantes registrados con filtros opcionales y paginación. "
        "El orden por defecto es por id ascendente."
    ),
)
def list_voters(
    db: DbSession,
    has_voted: bool | None = Query(
        default=None, description="Filtra por votantes que ya emitieron su voto"
    ),
    search: str | None = Query(
        default=None, description="Búsqueda parcial e insensible a mayúsculas sobre name y email"
    ),
    page: int = Query(default=1, ge=1, description="Número de página (base 1)"),
    page_size: int = Query(
        default=10, ge=1, le=100, description="Cantidad de elementos por página"
    ),
) -> Page[VoterRead]:
    """Lista los votantes con filtros y paginación."""
    return voter_service.list_voters(
        db, has_voted=has_voted, search=search, page=page, page_size=page_size
    )


@router.get(
    "/{voter_id}",
    response_model=VoterRead,
    summary="Obtener un votante",
    description="Devuelve el votante con el id indicado.",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "El votante no existe",
        }
    },
)
def get_voter(voter_id: int, db: DbSession) -> VoterRead:
    """Devuelve el detalle de un votante."""
    return voter_service.get_voter(db, voter_id)


@router.delete(
    "/{voter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un votante",
    description=(
        "Elimina un votante que todavía no ha emitido su voto. Si ya votó, se "
        "responde 409 porque su voto forma parte de los resultados."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "El votante no existe",
        },
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El votante ya emitió su voto",
        },
    },
)
def delete_voter(voter_id: int, db: DbSession) -> Response:
    """Elimina un votante sin votos emitidos."""
    voter_service.delete_voter(db, voter_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
