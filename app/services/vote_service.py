"""Reglas de negocio de votación y cálculo de estadísticas."""

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import PageParams, paginate
from app.models.candidate import Candidate
from app.models.vote import Vote
from app.models.voter import Voter
from app.schemas.vote import CandidateStatistic, VoteCreate, VoteStatistics


def cast_vote(db: Session, data: VoteCreate) -> Vote:
    """Emite un voto dentro de una única transacción atómica (todo o nada).

    1. Bloquea la fila del votante y valida que exista y no haya votado.
    2. Valida que el candidato exista.
    3. Inserta el voto.
    4. Marca ``voter.has_voted = True``.
    5. Incrementa ``candidate.votes`` con una expresión SQL atómica.
    6. Confirma la transacción; ante cualquier error se revierte.
    """
    try:
        voter = db.execute(
            select(Voter).where(Voter.id == data.voter_id).with_for_update()
        ).scalar_one_or_none()
        if voter is None:
            raise NotFoundError(f"El votante con id {data.voter_id} no existe")
        if voter.has_voted:
            raise ConflictError(f"El votante {data.voter_id} ya ha emitido su voto")

        candidate = db.execute(
            select(Candidate).where(Candidate.id == data.candidate_id)
        ).scalar_one_or_none()
        if candidate is None:
            raise NotFoundError(f"El candidato con id {data.candidate_id} no existe")

        vote = Vote(voter_id=voter.id, candidate_id=candidate.id)
        db.add(vote)

        voter.has_voted = True
        db.execute(
            update(Candidate)
            .where(Candidate.id == candidate.id)
            .values(votes=Candidate.votes + 1)
            .execution_options(synchronize_session="fetch")
        )

        db.commit()
    except IntegrityError as exc:
        # La restricción UNIQUE de votes.voter_id saltó: voto duplicado.
        db.rollback()
        raise ConflictError(f"El votante {data.voter_id} ya ha emitido su voto") from exc
    except Exception:
        db.rollback()
        raise

    db.refresh(vote)
    return vote


def list_votes(db: Session, *, page: int = 1, page_size: int = 10) -> dict:
    """Lista los votos emitidos, ordenados por id ascendente."""
    stmt = select(Vote).order_by(Vote.id.asc())
    return paginate(db, stmt, PageParams(page=page, page_size=page_size))


def get_statistics(db: Session) -> VoteStatistics:
    """Calcula las estadísticas de la votación con consultas agregadas en SQL."""
    total_votes = db.execute(select(func.count()).select_from(Vote)).scalar_one()
    total_voters_registered = db.execute(select(func.count()).select_from(Voter)).scalar_one()
    total_voters_who_voted = db.execute(
        select(func.count()).select_from(Voter).where(Voter.has_voted.is_(True))
    ).scalar_one()

    rows = db.execute(
        select(
            Candidate.id.label("candidate_id"),
            Candidate.name.label("name"),
            Candidate.party.label("party"),
            func.count(Vote.id).label("votes"),
        )
        .outerjoin(Vote, Vote.candidate_id == Candidate.id)
        .group_by(Candidate.id, Candidate.name, Candidate.party)
        .order_by(func.count(Vote.id).desc(), Candidate.id.asc())
    ).all()

    candidates = [
        CandidateStatistic(
            candidate_id=row.candidate_id,
            name=row.name,
            party=row.party,
            votes=row.votes,
            percentage=(
                round(row.votes / total_votes * 100, 2) if total_votes else 0.0
            ),
        )
        for row in rows
    ]

    participation_percentage = (
        round(total_voters_who_voted / total_voters_registered * 100, 2)
        if total_voters_registered
        else 0.0
    )

    return VoteStatistics(
        total_votes=total_votes,
        total_voters_registered=total_voters_registered,
        total_voters_who_voted=total_voters_who_voted,
        participation_percentage=participation_percentage,
        candidates=candidates,
    )
