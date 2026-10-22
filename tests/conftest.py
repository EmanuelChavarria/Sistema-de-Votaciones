"""Configuración de las pruebas: SQLite en memoria y cliente HTTP de test."""

import os

# La configuración debe existir ANTES de importar la aplicación: pydantic-settings
# lee las variables de entorno al construir el objeto Settings.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault(
    "SECRET_KEY", "clave-de-pruebas-unica-para-el-sistema-de-votaciones-2026"
)
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("FIRST_ADMIN_USERNAME", "admin")
os.environ.setdefault("FIRST_ADMIN_PASSWORD", "Admin12345")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_USERNAME = "tester"
TEST_PASSWORD = "Test12345"

# Motor SQLite en memoria compartido entre sesiones (StaticPool) para que todas
# las peticiones de un test vean la misma base de datos.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


@pytest.fixture
def db_session() -> Session:
    """Sesión de base de datos aislada para cada test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Cliente HTTP con la dependencia ``get_db`` sustituida por la sesión de test."""
    def override_get_db() -> Session:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # No se usa `with TestClient(app)`: de ese modo no se dispara el lifespan, que
    # crearía las tablas en el engine de la aplicación y no en el de pruebas.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    """Usuario registrado en el sistema."""
    response = client.post(
        "/auth/register",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def auth_token(client: TestClient, registered_user: dict) -> str:
    """Token JWT de acceso válido."""
    response = client.post(
        "/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Cabecera ``Authorization`` lista para usar en las peticiones."""
    return {"Authorization": f"Bearer {auth_token}"}
