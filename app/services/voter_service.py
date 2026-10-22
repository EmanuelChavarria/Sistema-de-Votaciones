"""Reglas de negocio de votantes."""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import PageParams, paginate
from app.core.text import has_normalized_match
from app.models.candidate import Candidate
from app.models.voter import Voter
from app.schemas.voter import VoterCreate


def get_voter(db: Session, voter_id: int) -> Voter:
    """Devuelve un votante por id o lanza :class:`NotFoundError`."""
    voter = db.get(Voter, voter_id)
    if voter is None:
        raise NotFoundError(f"El votante con id {voter_id} no existe")
    return voter


def get_voter_by_email(db: Session, email: str) -> Voter | None:
    """Busca un votante por email (los emails se guardan en minúsculas)."""
    return db.execute(
        select(Voter).where(Voter.email == email.strip().lower())
    ).scalar_one_or_none()


def create_voter(db: Session, data: VoterCreate) -> Voter:
    """Registra un votante nuevo.

    Lanza :class:`ConflictError` si el email ya existe o si el nombre coincide con
    el de un candidato ya registrado.
    """
    if get_voter_by_email(db, data.email) is not None:
        raise ConflictError(f"Ya existe un votante registrado con el email '{data.email}'")

    candidate_names = db.execute(select(Candidate.name)).scalars().all()
    if has_normalized_match(candidate_names, data.name):
        raise ConflictError(
            f"No se puede registrar el votante '{data.name}': ya existe un candidato "
            "registrado con ese nombre"
        )

    voter = Voter(name=data.name, email=data.email, has_voted=False)
    db.add(voter)
    try:
        db.commit()
    except IntegrityError as exc:
        # Carrera entre dos altas simultáneas con el mismo email.
        db.rollback()
        raise ConflictError(f"Ya existe un votante registrado con el email '{data.email}'") from exc
    db.refresh(voter)
    return voter


def list_voters(
    db: Session,
    *,
    has_voted: bool | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Lista votantes con filtros y paginación, ordenados por id ascendente."""
    stmt = select(Voter)

    if has_voted is not None:
        stmt = stmt.where(Voter.has_voted.is_(has_voted))

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Voter.name.ilike(pattern), Voter.email.ilike(pattern))
        )

    stmt = stmt.order_by(Voter.id.asc())
    return paginate(db, stmt, PageParams(page=page, page_size=page_size))


def delete_voter(db: Session, voter_id: int) -> None:
    """Elimina un votante que todavía no ha votado."""
    voter = get_voter(db, voter_id)
    if voter.has_voted:
        raise ConflictError(
            f"No se puede eliminar el votante {voter_id} porque ya emitió su voto "
            "y ese voto forma parte de los resultados"
        )
    db.delete(voter)
    db.commit()
