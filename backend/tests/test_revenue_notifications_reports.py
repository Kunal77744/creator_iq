"""Regression tests for Revenue, Notifications, and Reports endpoints."""
from .conftest import auth, register


# ---------- Revenue ----------
def test_revenue_requires_auth(client):
    assert client.get("/api/revenue").status_code == 401
    assert client.post("/api/revenue", json={"title": "Deal", "amount": 1000}).status_code == 401


def test_revenue_crud_and_summary(client, h):
    # Initial GET seeds sample ledger or returns summary
    r = client.get("/api/revenue", headers=h["creator"])
    assert r.status_code == 200
    initial = r.json()
    assert "summary" in initial and "entries" in initial
    initial_count = len(initial["entries"])

    # Create new entry
    created = client.post(
        "/api/revenue",
        json={
            "source": "sponsorship",
            "title": "Vercel Launch Sponsor",
            "platform": "YouTube",
            "amount": 50000,
            "status": "paid",
        },
        headers=h["creator"],
    )
    assert created.status_code == 201
    entry_id = created.json()["revenue_id"]

    # Verify list updated
    after = client.get("/api/revenue", headers=h["creator"]).json()
    assert len(after["entries"]) == initial_count + 1

    # Delete entry
    deleted = client.delete(f"/api/revenue/{entry_id}", headers=h["creator"])
    assert deleted.status_code == 204


def test_revenue_cross_user_isolation(client, h):
    created = client.post(
        "/api/revenue",
        json={"source": "ad_revenue", "title": "Private Payout", "amount": 1200},
        headers=h["creator"],
    )
    assert created.status_code == 201
    entry_id = created.json()["revenue_id"]

    register(client, email="other_creator@example.com", role="creator")
    other_h = auth(client, "other_creator@example.com", "Pass1234")
    r = client.delete(f"/api/revenue/{entry_id}", headers=other_h)
    assert r.status_code == 404


def test_revenue_invalid_amount(client, h):
    r = client.post("/api/revenue", json={"title": "Bad", "amount": -100}, headers=h["creator"])
    assert r.status_code == 422


# ---------- Notifications ----------
def test_notifications_requires_auth(client):
    assert client.get("/api/notifications").status_code == 401


def test_notifications_list_and_mark_read(client, h):
    r = client.get("/api/notifications", headers=h["creator"])
    assert r.status_code == 200
    body = r.json()
    assert body["unread_count"] > 0
    first_id = body["items"][0]["notification_id"]

    p = client.patch(f"/api/notifications/{first_id}/read", headers=h["creator"])
    assert p.status_code == 200

    all_r = client.post("/api/notifications/read-all", headers=h["creator"])
    assert all_r.status_code == 200

    after = client.get("/api/notifications", headers=h["creator"]).json()
    assert after["unread_count"] == 0


# ---------- Reports ----------
def test_reports_export_requires_auth(client):
    assert client.get("/api/reports/export?report_type=analytics").status_code == 401


def test_reports_export_csv_types(client, h):
    for rtype in ("analytics", "revenue", "platforms"):
        r = client.get(f"/api/reports/export?report_type={rtype}", headers=h["creator"])
        assert r.status_code == 200, rtype
        assert "text/csv" in r.headers["content-type"]
        assert f"creatoriq_{rtype}_report.csv" in r.headers["content-disposition"]


def test_reports_export_invalid_type(client, h):
    r = client.get("/api/reports/export?report_type=unknown", headers=h["creator"])
    assert r.status_code == 422
