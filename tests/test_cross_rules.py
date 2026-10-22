"""Pruebas de las reglas cruzadas entre votantes y candidatos.

Un votante no puede ser candidato y viceversa. La comparación se hace por nombre
normalizado (sin espacios sobrantes y sin distinguir mayúsculas).
"""


def test_create_voter_with_candidate_name_returns_409(client, auth_headers):
    client.post("/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers)

    response = client.post(
        "/voters",
        json={"name": "Carlos Ruiz", "email": "carlos@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert "detail" in response.json()


def test_create_candidate_with_voter_name_returns_409(client, auth_headers):
    client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    )

    response = client.post(
        "/candidates", json={"name": "Ana Torres"}, headers=auth_headers
    )
    assert response.status_code == 409
    assert "detail" in response.json()


def test_normalized_names_are_compared(client, auth_headers):
    """La comparación ignora mayúsculas y espacios sobrantes."""
    client.post("/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers)

    response = client.post(
        "/voters",
        json={"name": "  carlos   RUIZ  ", "email": "otro@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_different_names_are_allowed(client, auth_headers):
    client.post("/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers)

    response = client.post(
        "/voters",
        json={"name": "Carlos Ruíz", "email": "carlos@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 201
