"""Configuración de la aplicación leída desde variables de entorno (``.env``)."""

from functools import lru_cache

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración central de la API.

    Todos los valores sensibles provienen del entorno; nunca se hardcodean.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Aplicación ---
    PROJECT_NAME: str = "API de Sistema de Votaciones"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "API RESTful para gestionar un sistema de votaciones: votantes, candidatos "
        "y votos. Garantiza que cada votante emita un único voto y expone estadísticas "
        "de los resultados.\n\n"
        "**Autenticación:** todos los endpoints de `/voters`, `/candidates` y `/votes` "
        "requieren un token JWT. Registra un usuario en `POST /auth/register`, obtiene "
        "el token en `POST /auth/login` y úsalo con el botón **Authorize** de esta "
        "documentación o con la cabecera `Authorization: Bearer <token>`."
    )

    # --- Base de datos ---
    # Cambiar esta variable a `sqlite:///./votaciones.db` permite usar SQLite.
    DATABASE_URL: str = "sqlite:///./votaciones.db"

    # --- Seguridad / JWT ---
    # `SECRET_KEY` es obligatoria: no tiene valor por defecto a propósito.
    SECRET_KEY: str = Field(min_length=16, description="Clave secreta usada para firmar los JWT")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Datos iniciales ---
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "Admin12345"


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración de la aplicación (cacheada por proceso)."""
    try:
        return Settings()
    except ValidationError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            "Configuración inválida: falta definir SECRET_KEY (mínimo 16 caracteres) "
            "o alguna variable obligatoria. Copia .env.example a .env y ajústalo."
        ) from exc
