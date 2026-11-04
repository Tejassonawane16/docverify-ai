import os

from tests.conftest import PDF, PNG, auth, create_staff, register, upload


def test_upload_pdf_and_list(client):
    token = register(client)
    r = upload(client, token)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["status"] == "uploaded"
    assert doc["version"] == 1
    docs = client.get("/api/documents", headers=auth(token)).json()
    assert [d["id"] for d in docs] == [doc["id"]]


def test_upload_png_allowed(client):
    token = register(client)
    assert upload(client, token, "id_document", "passport.png", PNG).status_code == 201


def test_upload_rejects_wrong_type(client):
    token = register(client)
    assert upload(client, token, name="virus.exe", content=b"MZ...").status_code == 415


def test_upload_rejects_fake_pdf(client):
    token = register(client)
    assert upload(client, token, name="fake.pdf", content=b"not a pdf").status_code == 415


def test_upload_rejects_large_file(client):
    token = register(client)
    big = PDF + b"0" * (10 * 1024 * 1024)
    assert upload(client, token, content=big).status_code == 413


def test_file_stored_under_random_name(client):
    token = register(client)
    doc_id = upload(client, token, name="my_transcript.pdf").json()["id"]
    files = os.listdir(os.environ["UPLOAD_DIR"])
    assert "my_transcript.pdf" not in files
    r = client.get(f"/api/documents/{doc_id}/file", headers=auth(token))
    assert r.status_code == 200
    assert r.content == PDF


def test_applicant_cannot_see_others_documents(client):
    a = register(client, "a@example.com")
    b = register(client, "b@example.com")
    doc_id = upload(client, a).json()["id"]
    assert client.get(f"/api/documents/{doc_id}", headers=auth(b)).status_code == 404
    assert client.get(f"/api/documents/{doc_id}/file", headers=auth(b)).status_code == 404
    assert client.get("/api/documents", headers=auth(b)).json() == []


def test_staff_cannot_upload(client):
    reviewer = create_staff(client)
    assert upload(client, reviewer).status_code == 403


def test_new_version_only_after_reviewer_request(client):
    applicant = register(client)
    reviewer = create_staff(client)
    doc_id = upload(client, applicant).json()["id"]
    files = {"file": ("new.pdf", PDF, "application/pdf")}
    r = client.post(f"/api/documents/{doc_id}/versions", headers=auth(applicant), files=files)
    assert r.status_code == 409

    client.post(
        f"/api/review/documents/{doc_id}/decision",
        headers=auth(reviewer),
        json={"decision": "needs_more_info", "comment": "IELTS certificate has expired."},
    )
    seen = client.get(f"/api/documents/{doc_id}", headers=auth(applicant)).json()
    assert seen["status"] == "needs_more_info"
    assert seen["reviewer_comment"] == "IELTS certificate has expired."

    r = client.post(f"/api/documents/{doc_id}/versions", headers=auth(applicant), files=files)
    assert r.status_code == 201
    new = r.json()
    assert new["version"] == 2 and new["previous_id"] == doc_id and new["status"] == "uploaded"
    current = client.get("/api/documents", headers=auth(applicant)).json()
    assert [d["id"] for d in current] == [new["id"]]
    everything = client.get("/api/documents?include_history=true", headers=auth(applicant)).json()
    assert len(everything) == 2


def test_delete_account_removes_documents_and_files(client):
    token = register(client)
    doc_id = upload(client, token).json()["id"]
    reviewer = create_staff(client)
    assert client.delete("/api/auth/me", headers=auth(token)).status_code == 204
    assert client.get(f"/api/documents/{doc_id}/file", headers=auth(reviewer)).status_code == 404
    assert os.listdir(os.environ["UPLOAD_DIR"]) == []
