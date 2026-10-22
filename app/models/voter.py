"""Modelo de votante."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Voter(Base):
    """Persona habilitada para votar. Solo puede emitir un único voto."""

    __tablename__ = "voters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    has_voted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - ayuda de depuración
        return f"<Voter id={self.id} name={self.name!r} has_voted={self.has_voted}>"
