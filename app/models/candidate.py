"""Modelo de candidato."""

from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Candidate(Base):
    """Candidato que puede recibir votos.

    ``votes`` es un contador desnormalizado que se incrementa dentro de la misma
    transacción que inserta el voto, y nunca puede ser negativo.
    """

    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    party: Mapped[str | None] = mapped_column(String(120), nullable=True)
    votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint("votes >= 0", name="ck_candidates_votes_non_negative"),
    )

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<Candidate id={self.id} name={self.name!r} votes={self.votes}>"
