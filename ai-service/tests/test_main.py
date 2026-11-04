from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok", "service": "ai-service"}


def test_config_is_read_from_environment(monkeypatch):
    from app import main

    monkeypatch.setenv("TOP_K", "6")
    main.get_settings.cache_clear()
    assert client.get("/config").json()["top_k"] == 6
    main.get_settings.cache_clear()


def test_verify_not_implemented_yet():
    assert client.post("/verify").status_code == 501
