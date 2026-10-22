"""Esquemas comunes: paginación genérica, error unificado y salud."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Respuesta paginada genérica reutilizada por todos los listados."""

    items: list[T] = Field(description="Elementos de la página actual")
    total: int = Field(ge=0, description="Total de elementos que cumplen el filtro")
    page: int = Field(ge=1, description="Página actual (base 1)")
    page_size: int = Field(ge=1, description="Cantidad de elementos por página")
    pages: int = Field(ge=0, description="Cantidad total de páginas")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 42,
                "page": 1,
                "page_size": 10,
                "pages": 5,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Formato único de error devuelto por la API."""

    detail: str = Field(description="Mensaje claro y accionable en español")

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "El votante con id 99 no existe"}}
    )


class HealthResponse(BaseModel):
    """Estado del servicio."""

    status: str = Field(default="ok", description="Estado del servicio")

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})


class ValidationErrorItem(BaseModel):
    """Detalle de un error de validación de Pydantic."""

    loc: list[str | int] = Field(description="Ubicación del campo con error")
    msg: str = Field(description="Descripción del error")
    type: str = Field(description="Tipo de error de Pydantic")


class ValidationErrorResponse(BaseModel):
    """Respuesta 422 estándar de FastAPI (formato de validación)."""

    detail: list[ValidationErrorItem] = Field(
        description="Lista de errores de validación detectados"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": [
                    {
                        "loc": ["body", "name"],
                        "msg": "String should have at least 2 characters",
                        "type": "string_too_short",
                    }
                ]
            }
        }
    )
