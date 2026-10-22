"""Pruebas de los endpoints de candidatos."""

def test_create_candidate_returns_201(client, auth_headers):
    response = client.post(
        "/candidates",
        json={"name": "Carlos Ruiz", "party": "Partido Verde"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Carlos Ruiz"
    assert body["party"] == "Partido Verde"
    assert body["votes"] == 0


def test_create_candidate_without_party_returns_null(client, auth_headers):
    response = client.post(
        "/candidates", json={"name": "Laura Gómez"}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["party"] is None


def test_create_candidate_with_empty_party_stores_null(client, auth_headers):
    response = client.post(
        "/candidates", json={"name": "Laura Gómez", "party": "   "}, headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["party"] is None


def test_create_candidate_rejects_votes_field(client, auth_headers):
    response = client.post(
        "/candidates",
        json={"name": "Carlos Ruiz", "votes": 99},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_candidate_requires_token(client):
    response = client.post("/candidates", json={"name": "Carlos Ruiz"})
    assert response.status_code == 401


def test_list_candidates_pagination(client, auth_headers):
    for index in range(3):
        client.post(
            "/candidates",
            json={"name": f"Candidato {index}", "party": "Partido Verde" if index else "Azul"},
            headers=auth_headers,
        )

    body = client.get("/candidates?page=1&page_size=2", headers=auth_headers).json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_list_candidates_filter_by_party(client, auth_headers):
    client.post(
        "/candidates", json={"name": "Carlos Ruiz", "party": "Partido Verde"}, headers=auth_headers
    )
    client.post(
        "/candidates", json={"name": "Pedro Díaz", "party": "Independiente"}, headers=auth_headers
    )

    exact = client.get("/candidates?party=Partido Verde", headers=auth_headers).json()
    assert exact["total"] == 1
    assert exact["items"][0]["name"] == "Carlos Ruiz"

    partial = client.get("/candidates?party=Verde", headers=auth_headers).json()
    assert partial["total"] == 1


def test_list_candidates_filter_by_search(client, auth_headers):
    client.post(
        "/candidates", json={"name": "Carlos Ruiz", "party": "Partido Verde"}, headers=auth_headers
    )
    client.post(
        "/candidates", json={"name": "Pedro Díaz", "party": "Independiente"}, headers=auth_headers
    )

    body = client.get("/candidates?search=ruiz", headers=auth_headers).json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Carlos Ruiz"


def test_get_candidate_returns_200_and_404(client, auth_headers):
    created = client.post(
        "/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers
    ).json()

    ok = client.get(f"/candidates/{created['id']}", headers=auth_headers)
    assert ok.status_code == 200
    assert ok.json()["name"] == "Carlos Ruiz"

    assert client.get("/candidates/9999", headers=auth_headers).status_code == 404


def test_delete_candidate_returns_204(client, auth_headers):
    created = client.post(
        "/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers
    ).json()

    response = client.delete(f"/candidates/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/candidates/{created['id']}", headers=auth_headers).status_code == 404


def test_delete_candidate_returns_404_when_missing(client, auth_headers):
    assert client.delete("/candidates/9999", headers=auth_headers).status_code == 404


def test_delete_candidate_with_votes_returns_409(client, auth_headers):
    candidate = client.post(
        "/candidates", json={"name": "Carlos Ruiz"}, headers=auth_headers
    ).json()
    voter = client.post(
        "/voters",
        json={"name": "Ana Torres", "email": "ana@example.com"},
        headers=auth_headers,
    ).json()
    vote = client.post(
        "/votes",
        json={"voter_id": voter["id"], "candidate_id": candidate["id"]},
        headers=auth_headers,
    )
    assert vote.status_code == 201

    response = client.delete(f"/candidates/{candidate['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert "detail" in response.json()
