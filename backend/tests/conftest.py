import os
import shutil
import tempfile

# Settings must be set before the app is imported.
_tmp = tempfile.mkdtemp(prefix="docverify-test-")
# Set TEST_DATABASE_URL to run the tests against PostgreSQL instead of SQLite
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp}/test.db")
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["ADMIN_EMAIL"] = "admin@test.local"
os.environ["ADMIN_PASSWORD"] = "Admin-Password-1"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-hs256-signing"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    shutil.rmtree(os.environ["UPLOAD_DIR"], ignore_errors=True)
    with TestClient(app) as c:  # lifespan creates tables and the admin
        yield c


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client, email="arjun@example.com", name="Arjun Mehta", password="Secure-Pass-1"):
    r = client.post(
        "/api/auth/register", json={"email": email, "full_name": name, "password": password}
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def login(client, email, password):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def admin_token(client):
    return login(client, "admin@test.local", "Admin-Password-1")


def create_staff(client, role="reviewer", email="katrin@example.org"):
    r = client.post(
        "/api/admin/users",
        headers=auth(admin_token(client)),
        json={
            "email": email,
            "full_name": "Katrin Weber",
            "password": "Reviewer-Pass-1",
            "role": role,
        },
    )
    assert r.status_code == 201, r.text
    return login(client, email, "Reviewer-Pass-1")


def upload(client, token, doc_type="transcript", name="transcript.pdf", content=PDF):
    return client.post(
        "/api/documents",
        headers=auth(token),
        data={"doc_type": doc_type},
        files={"file": (name, content, "application/octet-stream")},
    )
