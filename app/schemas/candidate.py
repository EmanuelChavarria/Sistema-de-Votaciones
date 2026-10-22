"""Esquemas de candidatos."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidateCreate(BaseModel):
    """Datos de alta de un candidato. ``votes`` no se acepta en la entrada."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "Carlos Ruiz", "party": "Partido Verde"}},
    )

    name: str = Field(min_length=2, max_length=120, description="Nombre del candidato")
    party: str | None = Field(
        default=None, max_length=120, description="Partido o agrupación (opcional)"
    )

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        """Elimina espacios sobrantes; un nombre de solo espacios es inválido."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("party", mode="before")
    @classmethod
    def _normalize_party(cls, value: object) -> object:
        """Una partido vacío se guarda como NULL."""
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class CandidateRead(BaseModel):
    """Candidato (salida)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 2,
                "name": "Carlos Ruiz",
                "party": "Partido Verde",
                "votes": 6,
            }
        },
    )

    id: int
    name: str
    party: str | None
    votes: int
