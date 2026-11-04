def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "backend"}


def test_openapi_docs_available(client):
    assert client.get("/openapi.json").json()["info"]["title"] == "DocVerify AI API"
