from app.database import SessionLocal
from app.models import Document
from tests.conftest import admin_token, auth, create_staff, register, upload


def test_applicant_cannot_open_dashboard(client):
    token = register(client)
    assert client.get("/api/review/documents", headers=auth(token)).status_code == 403


def test_dashboard_lists_filters_and_sorts(client):
    a = register(client, "a@example.com", "Alice Applicant")
    b = register(client, "b@example.com", "Bob Applicant")
    reviewer = create_staff(client)
    d1 = upload(client, a).json()["id"]
    d2 = upload(client, b, "degree_certificate").json()["id"]
    with SessionLocal() as db:  # simulate AI scores (filled by the AI service in Phase 3)
        db.get(Document, d1).ai_confidence = 90.0
        db.get(Document, d2).ai_confidence = 40.0
        db.commit()

    rows = client.get("/api/review/documents", headers=auth(reviewer)).json()
    assert {r["owner_name"] for r in rows} == {"Alice Applicant", "Bob Applicant"}

    rows = client.get("/api/review/documents?sort=confidence_asc", headers=auth(reviewer)).json()
    assert [r["id"] for r in rows] == [d2, d1]

    rows = client.get("/api/review/documents?q=alice", headers=auth(reviewer)).json()
    assert [r["id"] for r in rows] == [d1]

    client.post(
        f"/api/review/documents/{d1}/decision",
        headers=auth(reviewer),
        json={"decision": "verified"},
    )
    pending = client.get("/api/review/documents?status=pending", headers=auth(reviewer)).json()
    assert [r["id"] for r in pending] == [d2]
    verified = client.get("/api/review/documents?status=verified", headers=auth(reviewer)).json()
    assert [r["id"] for r in verified] == [d1]


def test_detail_shows_document_and_empty_ai_report(client):
    applicant = register(client)
    reviewer = create_staff(client)
    doc_id = upload(client, applicant).json()["id"]
    detail = client.get(f"/api/review/documents/{doc_id}", headers=auth(reviewer)).json()
    assert detail["owner_name"] == "Arjun Mehta"
    assert detail["ai_report"] is None
    assert detail["reviews"] == [] and detail["history"] == []
    assert client.get(f"/api/documents/{doc_id}/file", headers=auth(reviewer)).status_code == 200


def test_decision_requires_comment_for_reject_and_is_stored(client):
    applicant = register(client)
    reviewer = create_staff(client)
    doc_id = upload(client, applicant).json()["id"]
    url = f"/api/review/documents/{doc_id}/decision"
    r = client.post(url, headers=auth(reviewer), json={"decision": "rejected"})
    assert r.status_code == 422
    r = client.post(
        url,
        headers=auth(reviewer),
        json={"decision": "rejected", "comment": "Institution not recognised."},
    )
    assert r.status_code == 200
    detail = client.get(f"/api/review/documents/{doc_id}", headers=auth(reviewer)).json()
    assert detail["status"] == "rejected"
    assert detail["reviews"][0]["decision"] == "rejected"
    assert detail["reviews"][0]["reviewer_id"] is not None


def test_override_of_ai_requires_comment(client):
    applicant = register(client)
    reviewer = create_staff(client)
    doc_id = upload(client, applicant).json()["id"]
    with SessionLocal() as db:
        db.get(Document, doc_id).ai_recommendation = "rejected"
        db.commit()
    url = f"/api/review/documents/{doc_id}/decision"
    r = client.post(url, headers=auth(reviewer), json={"decision": "verified"})
    assert r.status_code == 422


def test_review_actions_are_audited(client):
    applicant = register(client)
    reviewer = create_staff(client)
    doc_id = upload(client, applicant).json()["id"]
    client.post(
        f"/api/review/documents/{doc_id}/decision",
        headers=auth(reviewer),
        json={"decision": "verified"},
    )
    admin = admin_token(client)
    actions = {e["action"] for e in client.get("/api/admin/audit", headers=auth(admin)).json()}
    assert {"document_upload", "review_decision"} <= actions
    stats = client.get("/api/admin/stats", headers=auth(admin)).json()
    assert stats["documents_by_status"]["verified"] == 1
    assert stats["reviews_total"] == 1
