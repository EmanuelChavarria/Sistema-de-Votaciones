"""Hash de contraseñas y creación/decodificación de tokens JWT."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

# bcrypt solo considera los primeros 72 bytes de la contraseña.
BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Comprueba una contraseña en texto plano contra su hash bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        # Contraseñas con más de 72 bytes o hashes inválidos no pueden verificarse.
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT firmado con ``sub`` (username), ``iat`` y ``exp``."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    """Decodifica y valida un token JWT devolviendo el ``sub`` (username).

    Lanza :class:`UnauthorizedError` si el token es inválido o ha expirado.
    """
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError(
            "El token de acceso ha expirado. Inicia sesión nuevamente."
        ) from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("El token de acceso no es válido.") from exc

    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("El token de acceso no es válido.")
    return str(subject)
