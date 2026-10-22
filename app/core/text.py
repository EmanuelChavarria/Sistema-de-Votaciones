"""Utilidades de texto compartidas por los servicios."""

from collections.abc import Iterable


def normalize_name(name: str) -> str:
    """Normaliza un nombre para poder compararlo con otro equivalente.

    Colapsa los espacios internos, elimina los de los extremos y aplica ``casefold()``
    para que la comparación no dependa de mayúsculas ni acentos mayúsculos.
    """
    return " ".join(name.split()).casefold()


def has_normalized_match(names: Iterable[str], target: str) -> bool:
    """Indica si algún nombre de la colección equivale a ``target``.

    La comparación se hace sobre el nombre normalizado, que es la regla de negocio
    compartida entre votantes y candidatos.
    """
    normalized = normalize_name(target)
    if not normalized:
        return False
    return any(normalize_name(name) == normalized for name in names)
