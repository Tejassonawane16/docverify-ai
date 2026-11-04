from tests.conftest import admin_token, auth, create_staff, login, register


def test_applicant_cannot_open_admin(client):
    token = register(client)
    assert client.get("/api/admin/users", headers=auth(token)).status_code == 403


def test_reviewer_cannot_open_admin(client):
    reviewer = create_staff(client)
    assert client.get("/api/admin/users", headers=auth(reviewer)).status_code == 403


def test_staff_login_after_creation(client):
    create_staff(client, "admin", "second.admin@example.org")
    assert login(client, "second.admin@example.org", "Reviewer-Pass-1")


def test_create_staff_duplicate_email_rejected(client):
    create_staff(client)
    r = client.post(
        "/api/admin/users",
        headers=auth(admin_token(client)),
        json={
            "email": "katrin@example.org",
            "full_name": "Someone",
            "password": "Another-Pass-1",
            "role": "reviewer",
        },
    )
    assert r.status_code == 409


def test_admin_changes_role_takes_effect_next_request(client):
    admin = admin_token(client)
    token = register(client)
    me = client.get("/api/auth/me", headers=auth(token)).json()
    assert client.get("/api/admin/users", headers=auth(token)).status_code == 403
    r = client.patch(f"/api/admin/users/{me['id']}", headers=auth(admin), json={"role": "admin"})
    assert r.json()["role"] == "admin"
    # Same token, new role - read from the database on every request
    assert client.get("/api/admin/users", headers=auth(token)).status_code == 200


def test_deactivated_user_is_locked_out(client):
    admin = admin_token(client)
    token = register(client)
    uid = client.get("/api/auth/me", headers=auth(token)).json()["id"]
    client.patch(f"/api/admin/users/{uid}", headers=auth(admin), json={"is_active": False})
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 401
    r = client.post(
        "/api/auth/login", json={"email": "arjun@example.com", "password": "Secure-Pass-1"}
    )
    assert r.status_code == 401


def test_admin_cannot_change_own_account(client):
    admin = admin_token(client)
    uid = client.get("/api/auth/me", headers=auth(admin)).json()["id"]
    r = client.patch(f"/api/admin/users/{uid}", headers=auth(admin), json={"role": "applicant"})
    assert r.status_code == 400


def test_audit_log_records_actions_and_has_no_delete(client):
    register(client)
    admin = admin_token(client)
    entries = client.get("/api/admin/audit", headers=auth(admin)).json()
    assert {"register", "login"} <= {e["action"] for e in entries}
    assert all(set(e) >= {"timestamp", "user_ref", "action", "result"} for e in entries)
    only = client.get("/api/admin/audit?action=register", headers=auth(admin)).json()
    assert len(only) == 1
    assert client.delete("/api/admin/audit", headers=auth(admin)).status_code == 405


def test_failed_login_is_audited(client):
    client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x" * 10})
    admin = admin_token(client)
    entries = client.get("/api/admin/audit?action=login", headers=auth(admin)).json()
    assert any(e["result"] == "failure" for e in entries)


def test_stats_counts_users(client):
    register(client)
    admin = admin_token(client)
    s = client.get("/api/admin/stats", headers=auth(admin)).json()
    assert s["users_by_role"]["applicant"] == 1
    assert s["users_by_role"]["admin"] == 1
