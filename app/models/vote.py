"""Modelo de voto."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utc_now() -> datetime:
    """Instante actual en UTC con zona horaria explícita."""
    return datetime.now(timezone.utc)


class Vote(Base):
    """Voto emitido por un votante a favor de un candidato.

    ``voter_id`` es UNIQUE: la base de datos garantiza que un votante no pueda
    tener más de un voto, incluso ante peticiones simultáneas.
    """

    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    voter_id: Mapped[int] = mapped_column(
        ForeignKey("voters.id", ondelete="RESTRICT"),
        unique=True,
        index=True,
        nullable=False,
    )
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<Vote id={self.id} voter_id={self.voter_id} candidate_id={self.candidate_id}>"
