"""Pruebas de los endpoints de votantes."""

import pytest


def test_create_voter_returns_201(client, auth_headers):
    response = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Ana Torres"
    assert body["email"] == "ana@example.com"
    assert body["has_voted"] is False


def test_create_voter_stores_email_in_lowercase(client, auth_headers):
    response = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ANA@Example.COM"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["email"] == "ana@example.com"


def test_create_voter_rejects_has_voted_field(client, auth_headers):
    response = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com", "has_voted": True},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_voter_rejects_blank_name(client, auth_headers):
    response = client.post(
        "/voters", json={"name": "   ", "email": "ana@example.com"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_create_voter_rejects_invalid_email(client, auth_headers):
    response = client.post(
        "/voters", json={"name": "Ana Torres", "email": "no-es-un-email"}, headers=auth_headers
    )
    assert response.status_code == 422


def test_create_voter_duplicate_email_returns_409(client, auth_headers):
    payload = {"name": "Ana Torres", "email": "ana@example.com"}
    assert client.post("/voters", json=payload, headers=auth_headers).status_code == 201
    response = client.post(
        "/voters",
        json={"name": "Otra Persona", "email": "ana@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert "detail" in response.json()


def test_create_voter_requires_token(client):
    response = client.post(
        "/voters", json={"name": "Ana Torres", "email": "ana@example.com"}
    )
    assert response.status_code == 401


def test_list_voters_pagination(client, auth_headers):
    for index in range(5):
        client.post(
            "/voters",
            json={"name": f"Votante {index}", "email": f"votante{index}@example.com"},
            headers=auth_headers,
        )

    response = client.get("/voters?page=1&page_size=2", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["pages"] == 3
    assert [item["id"] for item in body["items"]] == sorted(
        item["id"] for item in body["items"]
    )


def test_list_voters_rejects_invalid_pagination(client, auth_headers):
    assert client.get("/voters?page=0", headers=auth_headers).status_code == 422
    assert client.get("/voters?page_size=101", headers=auth_headers).status_code == 422


def test_list_voters_filter_by_has_voted(client, auth_headers):
    voter = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    ).json()
    client.post(
        "/voters",
        json={"name": "Luis Peña", "email": "luis@example.com"},
        headers=auth_headers,
    )

    pending = client.get("/voters?has_voted=false", headers=auth_headers).json()
    assert pending["total"] == 2
    assert all(item["has_voted"] is False for item in pending["items"])

    voted = client.get("/voters?has_voted=true", headers=auth_headers).json()
    assert voted["total"] == 0
    assert voted["items"] == []
    assert voter["has_voted"] is False


def test_list_voters_search_is_case_insensitive(client, auth_headers):
    client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    )
    client.post(
        "/voters",
        json={"name": "Luis Peña", "email": "luis@example.com"},
        headers=auth_headers,
    )

    by_name = client.get("/voters?search=ANA", headers=auth_headers).json()
    assert by_name["total"] == 1
    assert by_name["items"][0]["name"] == "Ana Torres"

    by_email = client.get("/voters?search=luis@", headers=auth_headers).json()
    assert by_email["total"] == 1
    assert by_email["items"][0]["email"] == "luis@example.com"


def test_get_voter_returns_200_and_404(client, auth_headers):
    created = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    ).json()

    ok = client.get(f"/voters/{created['id']}", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["email"] == "ana@example.com"

    missing = client.get("/voters/9999", headers=auth_headers)
    assert missing.status_code == 404
    assert "detail" in missing.json()


def test_delete_voter_returns_204(client, auth_headers):
    created = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    ).json()

    response = client.delete(f"/voters/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/voters/{created['id']}", headers=auth_headers).status_code == 404


def test_delete_voter_returns_404_when_missing(client, auth_headers):
    assert client.delete("/voters/9999", headers=auth_headers).status_code == 404


def test_delete_voter_with_vote_returns_409(client, auth_headers):
    voter = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    ).json()
    candidate = client.post(
        "/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers
    ).json()
    vote = client.post(
        "/votes",
        json={"voter_id": voter["id"], "candidate_id": candidate["id"]},
        headers=auth_headers,
    )
    assert vote.status_code == 201

    response = client.delete(f"/voters/{voter['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert "detail" in response.json()
