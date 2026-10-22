"""Carga de datos iniciales: usuario administrador y datos de demostración.

Uso:  python -m app.scripts.seed
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.models.voter import Voter
from app.schemas.vote import VoteCreate
from app.services.auth_service import ensure_admin_user
from app.services.vote_service import cast_vote

DEMO_CANDIDATES: list[tuple[str, str | None]] = [
    ("Carlos Ruiz", "Partido Verde"),
    ("Laura Gómez", None),
    ("Pedro Díaz", "Independiente"),
]

DEMO_VOTERS: list[tuple[str, str]] = [
    ("Ana Torres", "ana@example.com"),
    ("Luis Fernández", "luis@example.com"),
    ("Sofía Ramírez", "sofia@example.com"),
    ("Miguel Ángel Castro", "miguel@example.com"),
    ("Elena Morales", "elena@example.com"),
]

DEMO_VOTES: list[tuple[str, str]] = [
    ("Ana Torres", "Carlos Ruiz"),
    ("Luis Fernández", "Carlos Ruiz"),
    ("Sofía Ramírez", "Pedro Díaz"),
    ("Miguel Ángel Castro", "Laura Gómez"),
    ("Elena Morales", "Carlos Ruiz"),
]


def seed_demo_data(db: Session) -> None:
    """Crea candidatos, votantes y votos de demostración si no existen."""
    candidates: dict[str, Candidate] = {}
    for name, party in DEMO_CANDIDATES:
        candidate = db.execute(
            select(Candidate).where(Candidate.name == name)
        ).scalar_one_or_none()
        if candidate is None:
            candidate = Candidate(name=name, party=party, votes=0)
            db.add(candidate)
            db.flush()
        candidates[name] = candidate

    voters: dict[str, Voter] = {}
    for name, email in DEMO_VOTERS:
        voter = db.execute(
            select(Voter).where(Voter.email == email)
        ).scalar_one_or_none()
        if voter is None:
            voter = Voter(name=name, email=email, has_voted=False)
            db.add(voter)
            db.flush()
        voters[name] = voter

    db.commit()

    for voter_name, candidate_name in DEMO_VOTES:
        voter = voters[voter_name]
        candidate = candidates[candidate_name]
        if voter.has_voted:
            continue
        cast_vote(db, VoteCreate(voter_id=voter.id, candidate_id=candidate.id))


def main() -> None:
    """Crea el usuario administrador inicial y carga los datos de demostración."""
    settings = get_settings()
    with SessionLocal() as db:
        admin = ensure_admin_user(
            db, settings.FIRST_ADMIN_USERNAME, settings.FIRST_ADMIN_PASSWORD
        )
        print(f"Usuario administrador listo: {admin.username}")
        seed_demo_data(db)
        print("Datos de demostración cargados (3 candidatos, 5 votantes, 5 votos).")


if __name__ == "__main__":
    main()
