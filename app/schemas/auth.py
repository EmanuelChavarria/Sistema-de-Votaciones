"""Esquemas de autenticación y usuarios."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import BCRYPT_MAX_BYTES


class UserRegister(BaseModel):
    """Datos de registro de un usuario del sistema."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"username": "admin", "password": "Admin12345"}},
    )

    username: str = Field(
        min_length=3, max_length=50, description="Nombre de usuario único (3 a 50 caracteres)"
    )
    password: str = Field(
        min_length=8,
        max_length=BCRYPT_MAX_BYTES,
        description="Contraseña en texto plano (mínimo 8 caracteres)",
    )

    @field_validator("username", mode="before")
    @classmethod
    def _normalize_username(cls, value: object) -> object:
        """Normaliza el nombre de usuario para que el login no sea ambiguo."""
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("password")
    @classmethod
    def _check_password_size(cls, value: str) -> str:
        """bcrypt solo procesa los primeros 72 bytes de la contraseña."""
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(f"La contraseña no puede superar los {BCRYPT_MAX_BYTES} bytes")
        return value


class UserRead(BaseModel):
    """Usuario del sistema (salida). Nunca incluye el hash de la contraseña."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_active: bool


class Token(BaseModel):
    """Respuesta de inicio de sesión."""

    access_token: str = Field(description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"}
        }
    )
