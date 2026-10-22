"""Esquemas de votantes."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.networks import EmailStr


class VoterCreate(BaseModel):
    """Datos de alta de un votante. ``has_voted`` no se acepta en la entrada."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"name": "Ana Torres", "email": "ana@example.com"}},
    )

    name: str = Field(min_length=2, max_length=120, description="Nombre completo del votante")
    email: EmailStr = Field(description="Correo electrónico único del votante")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        """Elimina espacios sobrantes; un nombre de solo espacios es inválido."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        """Guarda los emails siempre en minúsculas."""
        if isinstance(value, str):
            return value.strip().lower()
        return value


class VoterRead(BaseModel):
    """Votante (salida)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Ana Torres",
                "email": "ana@example.com",
                "has_voted": False,
            }
        },
    )

    id: int
    name: str
    email: str
    has_voted: bool
