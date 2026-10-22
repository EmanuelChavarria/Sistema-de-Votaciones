"""Reglas de negocio de autenticación y usuarios."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserRegister


def get_user_by_username(db: Session, username: str) -> User | None:
    """Busca un usuario por nombre (comparación insensible a mayúsculas)."""
    return db.execute(
        select(User).where(func.lower(User.username) == username.strip().lower())
    ).scalar_one_or_none()


def register_user(db: Session, data: UserRegister) -> User:
    """Crea un usuario del sistema.

    Lanza :class:`ConflictError` si el nombre de usuario ya está registrado.
    """
    if get_user_by_username(db, data.username) is not None:
        raise ConflictError(f"El nombre de usuario '{data.username}' ya está registrado")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Carrera entre dos registros simultáneos con el mismo username.
        db.rollback()
        raise ConflictError(f"El nombre de usuario '{data.username}' ya está registrado") from exc
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    """Valida las credenciales de un usuario.

    Lanza :class:`UnauthorizedError` con un mensaje genérico para no revelar si el
    usuario existe o no.
    """
    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise UnauthorizedError("Credenciales inválidas")
    if not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Credenciales inválidas")
    return user


def ensure_admin_user(db: Session, username: str, password: str) -> User:
    """Crea el usuario administrador inicial si todavía no existe."""
    existing = get_user_by_username(db, username)
    if existing is not None:
        return existing
    return register_user(
        db, UserRegister(username=username, password=password)
    )
