"""Reglas de negocio de candidatos."""

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import PageParams, paginate
from app.core.text import has_normalized_match
from app.models.candidate import Candidate
from app.models.voter import Voter
from app.schemas.candidate import CandidateCreate


def get_candidate(db: Session, candidate_id: int) -> Candidate:
    """Devuelve un candidato por id o lanza :class:`NotFoundError`."""
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise NotFoundError(f"El candidato con id {candidate_id} no existe")
    return candidate


def create_candidate(db: Session, data: CandidateCreate) -> Candidate:
    """Registra un candidato nuevo.

    Lanza :class:`ConflictError` si el nombre coincide con el de un votante ya
    registrado.
    """
    voter_names = db.execute(select(Voter.name)).scalars().all()
    if has_normalized_match(voter_names, data.name):
        raise ConflictError(
            f"No se puede registrar el candidato '{data.name}': ya existe un votante "
            "registrado con ese nombre"
        )

    candidate = Candidate(name=data.name, party=data.party, votes=0)
    db.add(candidate)
    try:
        db.commit()
    except IntegrityError as exc:  # pragma: no cover - salvaguarda
        db.rollback()
        raise ConflictError(f"No se pudo registrar el candidato '{data.name}'") from exc
    db.refresh(candidate)
    return candidate


def list_candidates(
    db: Session,
    *,
    party: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Lista candidatos con filtros y paginación, ordenados por id ascendente."""
    stmt = select(Candidate)

    if party and party.strip():
        pattern = f"%{party.strip()}%"
        stmt = stmt.where(Candidate.party.ilike(pattern))

    if search and search.strip():
        stmt = stmt.where(Candidate.name.ilike(f"%{search.strip()}%"))

    stmt = stmt.order_by(Candidate.id.asc())
    return paginate(db, stmt, PageParams(page=page, page_size=page_size))


def delete_candidate(db: Session, candidate_id: int) -> None:
    """Elimina un candidato que todavía no tiene votos."""
    candidate = get_candidate(db, candidate_id)
    if candidate.votes > 0:
        raise ConflictError(
            f"No se puede eliminar el candidato {candidate_id} porque tiene "
            f"{candidate.votes} voto(s) y esos votos forman parte de los resultados"
        )
    db.delete(candidate)
    db.commit()
