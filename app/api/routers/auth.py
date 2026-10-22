"""Endpoints de autenticación: registro e inicio de sesión."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession
from app.core.security import create_access_token
from app.schemas.auth import Token, UserRead, UserRegister
from app.schemas.common import ErrorResponse, ValidationErrorResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario",
    description=(
        "Crea un usuario del sistema. El `username` se normaliza a minúsculas y "
        "debe ser único; la contraseña debe tener al menos 8 caracteres."
    ),
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "El nombre de usuario ya está registrado",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Datos de registro inválidos",
        },
    },
)
def register(payload: UserRegister, db: DbSession) -> UserRead:
    """Registra un usuario nuevo del sistema."""
    return auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    description=(
        "Autentica a un usuario y devuelve un token JWT de acceso. Envía los datos "
        "como `form-data` con los campos `username` y `password`."
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "Credenciales inválidas",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ValidationErrorResponse,
            "description": "Faltan los campos username o password",
        },
    },
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> Token:
    """Inicia sesión y devuelve el token JWT de acceso."""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    return Token(access_token=create_access_token(subject=user.username), token_type="bearer")
