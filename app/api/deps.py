"""Dependencias de la API: esquema OAuth2 y usuario autenticado."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_username


class BearerToken(OAuth2PasswordBearer):
    """``OAuth2PasswordBearer`` con mensajes de error en español.

    Mantiene el esquema OpenAPI de OAuth2 (para que el botón **Authorize** de
    Swagger funcione) y responde 401 con la cabecera ``WWW-Authenticate: Bearer``.
    """

    async def __call__(self, request: Request) -> str:
        authorization = request.headers.get("Authorization")
        scheme, _, param = authorization.partition(" ") if authorization else ("", "", "")
        if not authorization or scheme.lower() != "bearer" or not param:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=(
                    "Falta el token de acceso. Inicia sesión en POST /auth/login y "
                    "envíalo en la cabecera Authorization: Bearer <token>."
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )
        return param


oauth2_scheme = BearerToken(tokenUrl="/auth/login", auto_error=True)

DbSession = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(token: TokenDep, db: DbSession) -> User:
    """Valida el token JWT y devuelve el usuario activo asociado.

    Lanza 401 si el token falta, es inválido, expiró o el usuario no existe o
    está desactivado.
    """
    try:
        username = decode_access_token(token)
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario del token no existe o está desactivado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
