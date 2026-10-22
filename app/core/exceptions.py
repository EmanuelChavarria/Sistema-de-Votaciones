"""Excepciones de dominio de la API.

Todas las errores de negocio se expresan con estas excepciones, que la aplicación
traduce a respuestas JSON con el formato unificado ``{"detail": "..."}``.
"""

from typing import Any


class DomainError(Exception):
    """Error de dominio con mensaje claro y accionable en español."""

    status_code: int = 500

    def __init__(self, detail: str, *, headers: dict[str, Any] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.headers: dict[str, Any] = headers or {}


class NotFoundError(DomainError):
    """El recurso solicitado no existe."""

    status_code = 404


class ConflictError(DomainError):
    """La operación entra en conflicto con el estado actual del recurso."""

    status_code = 409


class UnauthorizedError(DomainError):
    """Faltan credenciales o el token no es válido."""

    status_code = 401
