"""Module 1 test cases (the list from the mentor's guideline email)."""
from .conftest import auth, login, register


# ---------- registration ----------
def test_valid_registration(client):
    """Verify registration succeeds with 201 and omits password fields."""
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "creator" and body["role_label"] == "Creator"
    assert "password" not in body and "password_hash" not in body


def test_registration_creates_matching_profile(client):
    """Verify creator and agency registrations automatically create their profiles."""
    register(client, email="c1@example.com", role="creator")
    register(client, email="a1@example.com", role="agency", name="Agency One")
    assert client.get("/api/creators/me", headers=auth(client, "c1@example.com", "Pass1234")).status_code == 200
    assert client.get("/api/agencies/me", headers=auth(client, "a1@example.com", "Pass1234")).status_code == 200


def test_duplicate_registration(client):
    """Verify duplicate emails (case-insensitive) are rejected with 409."""
    assert register(client).status_code == 201
    assert register(client).status_code == 409
    assert register(client, email="NEW@Example.com").status_code == 409  # email is case-insensitive


def test_registration_invalid_or_missing_fields(client):
    """Verify invalid email, weak password, blank name, or unknown role fail with 422."""
    assert client.post("/api/auth/register", json={"email": "x@y.com"}).status_code == 422
    assert register(client, email="not-an-email").status_code == 422
    assert register(client, password="short1").status_code == 422
    assert register(client, password="onlyletters").status_code == 422
    assert register(client, password="12345678").status_code == 422
    assert register(client, name=" ").status_code == 422
    assert register(client, role="nonsense").status_code == 422


def test_cannot_register_as_admin_or_marketing(client):
    """Verify privileged roles cannot be self-assigned during public registration."""
    assert register(client, role="admin").status_code == 422
    assert register(client, role="marketing_team").status_code == 422


# ---------- login ----------
def test_valid_login_returns_token_and_role(client):
    """Verify valid login returns a bearer token and user role metadata."""
    r = login(client, "creator@creatoriq.com")
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["role"] == "creator"


def test_login_is_case_insensitive_on_email(client):
    """Verify login matches email addresses regardless of casing."""
    assert login(client, "Creator@CreatorIQ.com").status_code == 200


def test_invalid_login_credentials(client):
    """Verify wrong password and unknown email return identical 401 responses."""
    wrong_pw = login(client, "creator@creatoriq.com", "WrongPass1")
    unknown = login(client, "nobody@example.com", "Pass1234")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json()["detail"] == unknown.json()["detail"]  # same message, cannot probe emails


def test_login_missing_fields(client):
    """Verify login without a password fails validation with 422."""
    assert client.post("/api/auth/login", data={"username": "a@b.com"}).status_code == 422


# ---------- protected endpoints / authentication ----------
def test_protected_endpoint_without_token(client):
    """Verify protected endpoints reject unauthenticated requests with 401."""
    for path in ["/api/auth/me", "/api/creators/me", "/api/agencies/me", "/api/admin/users"]:
        assert client.get(path).status_code == 401, path


def test_invalid_or_tampered_token(client, h):
    """Verify malformed or modified JWT tokens are rejected with 401."""
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    token = h["creator"]["Authorization"].split()[1]
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401


def test_me_returns_current_user(client, h):
    """Verify /api/auth/me returns the authenticated user's details."""
    r = client.get("/api/auth/me", headers=h["agency"])
    assert r.status_code == 200 and r.json()["email"] == "agency@creatoriq.com"


# ---------- role-based access (authorization) ----------
def test_wrong_role_gets_403(client, h):
    """Verify role-restricted endpoints return 403 for unauthorized roles."""
    assert client.get("/api/admin/users", headers=h["creator"]).status_code == 403
    assert client.get("/api/admin/users", headers=h["agency"]).status_code == 403
    assert client.get("/api/admin/users", headers=h["marketing"]).status_code == 403
    assert client.get("/api/agencies/me", headers=h["creator"]).status_code == 403
    assert client.get("/api/creators/me", headers=h["agency"]).status_code == 403
    assert client.get("/api/creators/me", headers=h["marketing"]).status_code == 403


def test_admin_can_list_users(client, h):
    """Verify admin users can list all registered users."""
    r = client.get("/api/admin/users", headers=h["admin"])
    assert r.status_code == 200 and len(r.json()) == 4


def test_authenticated_is_not_the_same_as_admin(client, h):
    """Verify a non-admin user cannot escalate their own role to admin."""
    uid = client.get("/api/auth/me", headers=h["creator"]).json()["user_id"]
    r = client.patch(f"/api/admin/users/{uid}", json={"role": "admin"}, headers=h["creator"])
    assert r.status_code == 403  # a creator cannot promote themselves


def test_admin_changes_role_and_status(client, h):
    """Verify admins can update user roles and disable accounts."""
    register(client, email="x@example.com")
    users = client.get("/api/admin/users", headers=h["admin"]).json()
    uid = next(u["user_id"] for u in users if u["email"] == "x@example.com")
    r = client.patch(f"/api/admin/users/{uid}", json={"role": "marketing_team"}, headers=h["admin"])
    assert r.status_code == 200 and r.json()["role"] == "marketing_team"
    r = client.patch(f"/api/admin/users/{uid}", json={"is_active": False}, headers=h["admin"])
    assert r.json()["is_active"] is False
    assert login(client, "x@example.com", "Pass1234").status_code == 403  # disabled account


def test_admin_cannot_edit_self_or_set_invalid_role(client, h):
    """Verify admins cannot edit their own account via admin endpoints or assign invalid roles."""
    me = client.get("/api/auth/me", headers=h["admin"]).json()["user_id"]
    assert client.patch(f"/api/admin/users/{me}", json={"role": "creator"}, headers=h["admin"]).status_code == 400
    other = client.get("/api/auth/me", headers=h["creator"]).json()["user_id"]
    assert client.patch(f"/api/admin/users/{other}", json={"role": "god"}, headers=h["admin"]).status_code == 422
    assert client.patch("/api/admin/users/9999", json={"is_active": True}, headers=h["admin"]).status_code == 404


# ---------- creator profile ----------
def test_creator_updates_own_profile(client, h):
    """Verify creators can update their profile and partial updates preserve other fields."""
    r = client.put(
        "/api/creators/me",
        json={"creator_name": "Kunal", "bio": "I make tech videos", "website": "https://example.com", "location": "Bhopal"},
        headers=h["creator"],
    )
    assert r.status_code == 200
    assert r.json()["creator_name"] == "Kunal"
    # partial update leaves the other fields alone
    r = client.put("/api/creators/me", json={"bio": "New bio"}, headers=h["creator"])
    assert r.json()["bio"] == "New bio" and r.json()["creator_name"] == "Kunal"
    assert client.get("/api/creators/me", headers=h["creator"]).json()["location"] == "Bhopal"


def test_profile_validation(client, h):
    """Verify invalid website URLs, oversized bios, and javascript: URIs are rejected."""
    assert client.put("/api/creators/me", json={"website": "not a url"}, headers=h["creator"]).status_code == 422
    assert client.put("/api/creators/me", json={"bio": "x" * 1001}, headers=h["creator"]).status_code == 422
    assert client.put("/api/creators/me", json={"website": "javascript:alert(1)"}, headers=h["creator"]).status_code == 422


def test_creator_cannot_access_or_edit_another_creator(client, h):
    """Verify creators can view their own profile by ID but cannot view or edit others."""
    register(client, email="other@example.com", name="Other Creator")
    other_h = auth(client, "other@example.com", "Pass1234")
    other_id = client.get("/api/creators/me", headers=other_h).json()["creator_id"]
    my_id = client.get("/api/creators/me", headers=h["creator"]).json()["creator_id"]
    assert other_id != my_id
    assert client.get(f"/api/creators/{other_id}", headers=h["creator"]).status_code == 403
    assert client.put(f"/api/creators/{other_id}", json={"bio": "hacked"}, headers=h["creator"]).status_code == 403
    assert client.get(f"/api/creators/{my_id}", headers=h["creator"]).status_code == 200  # own profile by id is fine
    assert client.get("/api/creators/9999", headers=h["admin"]).status_code == 404


def test_agency_and_marketing_access_to_creator_profiles(client, h):
    """Verify linked agencies have read-only access, marketing has none, and admins have full access."""
    my_id = client.get("/api/creators/me", headers=h["creator"]).json()["creator_id"]
    # demo agency is linked to the demo creator -> allowed
    assert client.get(f"/api/creators/{my_id}", headers=h["agency"]).status_code == 200
    # marketing team has no access, admin does
    assert client.get(f"/api/creators/{my_id}", headers=h["marketing"]).status_code == 403
    assert client.get(f"/api/creators/{my_id}", headers=h["admin"]).status_code == 200
    # agency can read but not edit
    assert client.put(f"/api/creators/{my_id}", json={"bio": "x"}, headers=h["agency"]).status_code == 403
    assert client.put(f"/api/creators/{my_id}", json={"bio": "by admin"}, headers=h["admin"]).status_code == 200


def test_unlinked_agency_cannot_see_creator(client, h):
    """Verify an agency not linked to a creator receives 403 when accessing that creator."""
    register(client, email="a2@example.com", role="agency", name="Other Agency")
    a2 = auth(client, "a2@example.com", "Pass1234")
    my_id = client.get("/api/creators/me", headers=h["creator"]).json()["creator_id"]
    assert client.get(f"/api/creators/{my_id}", headers=a2).status_code == 403


# ---------- agency profile ----------
def test_agency_updates_own_profile(client, h):
    """Verify an agency can update its own profile fields."""
    r = client.put(
        "/api/agencies/me",
        json={"agency_name": "Bright Media", "description": "We manage creators", "website": "https://bright.example"},
        headers=h["agency"],
    )
    assert r.status_code == 200 and r.json()["agency_name"] == "Bright Media"


def test_agency_cannot_access_another_agency(client, h):
    """Verify agencies cannot view or edit another agency's profile while admins can."""
    register(client, email="a3@example.com", role="agency", name="Third Agency")
    a3 = auth(client, "a3@example.com", "Pass1234")
    other_id = client.get("/api/agencies/me", headers=a3).json()["agency_id"]
    assert client.get(f"/api/agencies/{other_id}", headers=h["agency"]).status_code == 403
    assert client.put(f"/api/agencies/{other_id}", json={"agency_name": "x"}, headers=h["agency"]).status_code == 403
    assert client.get(f"/api/agencies/{other_id}", headers=h["admin"]).status_code == 200


def test_agency_manages_its_creators(client, h):
    """Verify agencies can list, link, and unlink creators, with proper error codes."""
    assert len(client.get("/api/agencies/me/creators", headers=h["agency"]).json()) == 1
    register(client, email="c9@example.com", name="Nine")
    cid = client.get("/api/creators/me", headers=auth(client, "c9@example.com", "Pass1234")).json()["creator_id"]
    assert client.post("/api/agencies/me/creators", json={"creator_id": cid}, headers=h["agency"]).status_code == 201
    assert client.post("/api/agencies/me/creators", json={"creator_id": cid}, headers=h["agency"]).status_code == 409
    assert client.post("/api/agencies/me/creators", json={"creator_id": 9999}, headers=h["agency"]).status_code == 404
    assert client.delete(f"/api/agencies/me/creators/{cid}", headers=h["agency"]).status_code == 204
    assert client.delete(f"/api/agencies/me/creators/{cid}", headers=h["agency"]).status_code == 404
    assert client.post("/api/agencies/me/creators", json={"creator_id": cid}, headers=h["creator"]).status_code == 403


# ---------- account settings ----------
def test_update_own_name(client, h):
    """Verify users can update their display name and invalid inputs are rejected."""
    r = client.patch("/api/account/me", json={"name": "New Name"}, headers=h["creator"])
    assert r.status_code == 200 and r.json()["name"] == "New Name"
    assert client.patch("/api/account/me", json={"name": "A"}, headers=h["creator"]).status_code == 422
    assert client.patch("/api/account/me", json={"name": "New Name"}).status_code == 401


def test_change_password(client, h):
    """Verify password changes validate current/new passwords and update login credentials."""
    body = {"current_password": "Demo@1234", "new_password": "Better5678"}
    assert client.post("/api/account/change-password", json={**body, "current_password": "wrong"}, headers=h["creator"]).status_code == 400
    assert client.post("/api/account/change-password", json={**body, "new_password": "weak"}, headers=h["creator"]).status_code == 422
    assert client.post("/api/account/change-password", json={**body, "new_password": "Demo@1234"}, headers=h["creator"]).status_code == 400
    assert client.post("/api/account/change-password", json=body, headers=h["creator"]).status_code == 204
    assert login(client, "creator@creatoriq.com", "Demo@1234").status_code == 401
    assert login(client, "creator@creatoriq.com", "Better5678").status_code == 200


def test_deactivate_account(client, h):
    """Verify account deactivation invalidates tokens, blocks login, and prevents admin self-deactivation."""
    assert client.post("/api/account/deactivate", json={"password": "wrong"}, headers=h["creator"]).status_code == 400
    assert client.post("/api/account/deactivate", json={"password": "Demo@1234"}, headers=h["creator"]).status_code == 204
    assert client.get("/api/auth/me", headers=h["creator"]).status_code == 401  # old token stops working
    assert login(client, "creator@creatoriq.com").status_code == 403
    assert client.post("/api/account/deactivate", json={"password": "Demo@1234"}, headers=h["admin"]).status_code == 400
