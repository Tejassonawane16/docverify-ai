from app.database import SessionLocal
from app.models import User
from tests.conftest import auth, register


def test_register_creates_applicant_and_logs_in(client):
    token = register(client)
    me = client.get("/api/auth/me", headers=auth(token)).json()
    assert me["role"] == "applicant"
    assert me["email"] == "arjun@example.com"


def test_register_duplicate_email_rejected(client):
    register(client)
    r = client.post(
        "/api/auth/register",
        json={"email": "ARJUN@example.com", "full_name": "Other", "password": "Secure-Pass-1"},
    )
    assert r.status_code == 409


def test_register_short_password_rejected(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "full_name": "Ab", "password": "short"},
    )
    assert r.status_code == 422


def test_password_is_hashed(client):
    register(client)
    with SessionLocal() as db:
        user = db.query(User).filter_by(email="arjun@example.com").one()
        assert user.password_hash != "Secure-Pass-1"
        assert user.password_hash.startswith("$2")


def test_login_generic_error_for_unknown_email_and_wrong_password(client):
    register(client)
    a = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x" * 10})
    b = client.post("/api/auth/login", json={"email": "arjun@example.com", "password": "x" * 10})
    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"]


def test_lockout_after_five_failed_logins(client):
    register(client)
    for _ in range(5):
        client.post(
            "/api/auth/login", json={"email": "arjun@example.com", "password": "wrong-pass-1"}
        )
    r = client.post(
        "/api/auth/login", json={"email": "arjun@example.com", "password": "Secure-Pass-1"}
    )
    assert r.status_code == 429


def test_logout_invalidates_token(client):
    token = register(client)
    assert client.post("/api/auth/logout", headers=auth(token)).status_code == 204
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401


def test_protected_endpoint_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=auth("not-a-token")).status_code == 401
