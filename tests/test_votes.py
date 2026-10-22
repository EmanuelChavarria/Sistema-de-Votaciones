"""Pruebas de los endpoints de votos y de las estadísticas."""

import pytest


@pytest.fixture
def voter(client, auth_headers):
    return client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    ).json()


@pytest.fixture
def candidate(client, auth_headers):
    return client.post(
        "/candidates", json={"name": "Carlos Ruiz", "party": "Partido Verde"}, headers=auth_headers
    ).json()


def test_cast_vote_marks_voter_and_increments_candidate(
    client, auth_headers, voter, candidate
):
    response = client.post(
        "/votes",
        json={"voter_id": voter["id"], "candidate_id": candidate["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["voter_id"] == voter["id"]
    assert body["candidate_id"] == candidate["id"]
    assert body["created_at"]

    updated_voter = client.get(f"/voters/{voter['id']}", headers=auth_headers).json()
    assert updated_voter["has_voted"] is True

    updated_candidate = client.get(
        f"/candidates/{candidate['id']}", headers=auth_headers
    ).json()
    assert updated_candidate["votes"] == 1


def test_second_vote_from_same_voter_returns_409(client, auth_headers, voter, candidate):
    payload = {"voter_id": voter["id"], "candidate_id": candidate["id"]}
    assert client.post("/votes", json=payload, headers=auth_headers).status_code == 201

    response = client.post("/votes", json=payload, headers=auth_headers)
    assert response.status_code == 409
    assert "detail" in response.json()


def test_vote_with_unknown_voter_returns_404(client, auth_headers, candidate):
    response = client.post(
        "/votes",
        json={"voter_id": 9999, "candidate_id": candidate["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_vote_with_unknown_candidate_returns_404(client, auth_headers, voter):
    response = client.post(
        "/votes",
        json={"voter_id": voter["id"], "candidate_id": 9999},
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_failed_vote_does_not_change_counters(client, auth_headers, voter, candidate):
    """Atomicidad: un voto fallido no modifica ningún contador."""
    response = client.post(
        "/votes",
        json={"voter_id": voter["id"], "candidate_id": 9999},
        headers=auth_headers,
    )
    assert response.status_code == 404

    assert client.get(f"/voters/{voter['id']}", headers=auth_headers).json()["has_voted"] is False
    assert (
        client.get(f"/candidates/{candidate['id']}", headers=auth_headers).json()["votes"] == 0
    )
    assert client.get("/votes", headers=auth_headers).json()["total"] == 0


def test_vote_rejects_invalid_payload(client, auth_headers):
    response = client.post(
        "/votes", json={"voter_id": 0, "candidate_id": 1}, headers=auth_headers
    )
    assert response.status_code == 422


def test_vote_requires_token(client, voter, candidate):
    response = client.post(
        "/votes", json={"voter_id": voter["id"], "candidate_id": candidate["id"]}
    )
    assert response.status_code == 401


def test_list_votes_is_paginated(client, auth_headers, candidate):
    for index in range(3):
        created_voter = client.post(
            "/voters",
            json={"name": f"Votante {index}", "email": f"v{index}@example.com"},
            headers=auth_headers,
        ).json()
        client.post(
            "/votes",
            json={"voter_id": created_voter["id"], "candidate_id": candidate["id"]},
            headers=auth_headers,
        )

    body = client.get("/votes?page=1&page_size=2", headers=auth_headers).json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_statistics_without_votes_does_not_divide_by_zero(client, auth_headers):
    client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    )
    client.post("/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers)

    response = client.get("/votes/statistics", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_votes"] == 0
    assert body["total_voters_registered"] == 1
    assert body["total_voters_who_voted"] == 0
    assert body["participation_percentage"] == 0.0
    assert body["candidates"][0]["votes"] == 0
    assert body["candidates"][0]["percentage"] == 0.0


def test_statistics_with_votes(client, auth_headers):
    candidates = [
        client.post(
            "/candidates", json={"name": f"Candidato {index}"}, headers=auth_headers
        ).json()
        for index in range(3)
    ]
    for index in range(5):
        created_voter = client.post(
            "/voters",
            json={"name": f"Votante {index}", "email": f"v{index}@example.com"},
            headers=auth_headers,
        ).json()
        client.post(
            "/votes",
            json={
                "voter_id": created_voter["id"],
                "candidate_id": candidates[index % 3]["id"],
            },
            headers=auth_headers,
        )

    body = client.get("/votes/statistics", headers=auth_headers).json()
    assert body["total_votes"] == 5
    assert body["total_voters_registered"] == 5
    assert body["total_voters_who_voted"] == 5
    assert body["participation_percentage"] == 100.0
    assert len(body["candidates"]) == 3

    # Ordenados por votos descendente.
    votes = [candidate["votes"] for candidate in body["candidates"]]
    assert votes == sorted(votes, reverse=True)

    total_percentage = sum(candidate["percentage"] for candidate in body["candidates"])
    assert round(total_percentage, 2) == 100.0
    assert body["candidates"][0]["votes"] == 2
    assert body["candidates"][0]["percentage"] == 40.0


def test_statistics_includes_candidates_without_votes(client, auth_headers):
    client.post("/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers)
    client.post("/candidates", json={"name": "Pedro Díaz"}, headers=auth_headers)

    body = client.get("/votes/statistics", headers=auth_headers).json()
    assert len(body["candidates"]) == 2
    assert all(candidate["votes"] == 0 for candidate in body["candidates"])


def test_statistics_requires_token(client):
    assert client.get("/votes/statistics").status_code == 401
