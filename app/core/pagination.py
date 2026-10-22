"""Helper de paginación reutilizado por todos los listados de la API."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class PageParams:
    """Parámetros de paginación validados por el router."""

    page: int = 1
    page_size: int = 10

    @property
    def offset(self) -> int:
        """Cantidad de registros a saltar según la página solicitada."""
        return (self.page - 1) * self.page_size


def paginate(db: Session, stmt: Any, params: PageParams) -> dict[str, Any]:
    """Ejecuta la consulta paginada y devuelve la respuesta estándar ``Page[T]``.

    El total se calcula con una consulta de conteo sobre el mismo filtro, de modo
    que ``total`` y ``pages`` siempre reflejen los filtros aplicados.
    """
    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()
    rows = db.execute(
        stmt.offset(params.offset).limit(params.page_size)
    ).scalars().all()
    pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
    return {
        "items": list(rows),
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "pages": pages,
    }
