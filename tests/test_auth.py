"""Pruebas de los endpoints de autenticación."""

from tests.conftest import TEST_PASSWORD, TEST_USERNAME


def test_register_creates_active_user(client):
    response = client.post(
        "/auth/register", json={"username": "nuevo", "password": "Clave12345"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "nuevo"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_normalizes_username(client):
    response = client.post(
        "/auth/register", json={"username": "  MiUsuario  ", "password": "Clave12345"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "miusuario"


def test_register_duplicate_username_returns_409(client, registered_user):
    response = client.post(
        "/auth/register", json={"username": TEST_USERNAME, "password": "OtraClave123"}
    )
    assert response.status_code == 409
    assert "detail" in response.json()


def test_register_short_password_returns_422(client):
    response = client.post(
        "/auth/register", json={"username": "corto", "password": "123"}
    )
    assert response.status_code == 422


def test_register_rejects_unknown_fields(client):
    response = client.post(
        "/auth/register",
        json={"username": "extra", "password": "Clave12345", "is_admin": True},
    )
    assert response.status_code == 422


def test_login_returns_token(client, registered_user):
    response = client.post(
        "/auth/login", data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_with_wrong_password_returns_401(client, registered_user):
    response = client.post(
        "/auth/login", data={"username": TEST_USERNAME, "password": "PasswordIncorrecta"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_login_with_unknown_user_returns_generic_401(client):
    response = client.post(
        "/auth/login", data={"username": "noexiste", "password": "Clave12345"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_protected_endpoint_without_token_returns_401(client):
    response = client.get("/voters")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert "detail" in response.json()


def test_protected_endpoint_with_invalid_token_returns_401(client):
    response = client.get("/voters", headers={"Authorization": "Bearer token.invalido"})
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_protected_endpoint_with_valid_token_returns_200(client, auth_headers):
    response = client.get("/voters", headers=auth_headers)
    assert response.status_code == 200


def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
