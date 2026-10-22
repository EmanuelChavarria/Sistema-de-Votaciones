"""Esquemas de votos y estadísticas."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VoteCreate(BaseModel):
    """Datos para emitir un voto."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"voter_id": 1, "candidate_id": 2}},
    )

    voter_id: int = Field(gt=0, description="Id del votante que emite el voto")
    candidate_id: int = Field(gt=0, description="Id del candidato receptor del voto")


class VoteRead(BaseModel):
    """Voto registrado (salida)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "voter_id": 1,
                "candidate_id": 2,
                "created_at": "2026-10-21T15:04:05Z",
            }
        },
    )

    id: int
    voter_id: int
    candidate_id: int
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def _ensure_utc(cls, value: datetime) -> datetime:
        """Normaliza a UTC: SQLite devuelve datetimes naive."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class CandidateStatistic(BaseModel):
    """Resultado de un candidato dentro de las estadísticas."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "candidate_id": 2,
                "name": "Carlos Ruiz",
                "party": "Partido Verde",
                "votes": 6,
                "percentage": 60.0,
            }
        }
    )

    candidate_id: int
    name: str
    party: str | None
    votes: int
    percentage: float = Field(description="Porcentaje del total de votos (2 decimales)")


class VoteStatistics(BaseModel):
    """Estadísticas globales de la votación."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_votes": 10,
                "total_voters_registered": 25,
                "total_voters_who_voted": 10,
                "participation_percentage": 40.0,
                "candidates": [],
            }
        }
    )

    total_votes: int = Field(ge=0, description="Cantidad total de votos emitidos")
    total_voters_registered: int = Field(ge=0, description="Votantes registrados")
    total_voters_who_voted: int = Field(ge=0, description="Votantes que ya emitieron su voto")
    participation_percentage: float = Field(
        description="Porcentaje de participación de los votantes registrados"
    )
    candidates: list[CandidateStatistic] = Field(
        description="Resultado por candidato, ordenado por votos descendente"
    )
