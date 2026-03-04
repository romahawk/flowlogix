"""
Smoke tests — verify app starts and core routes respond.
These tests run with demo mode OFF and an in-memory SQLite DB.
"""


def test_login_page_loads(client):
    """GET /login returns 200 with the login form."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_root_redirects(client):
    """GET / redirects (to login when unauthenticated, demo off)."""
    resp = client.get("/")
    assert resp.status_code in (301, 302)


def test_api_orders_requires_auth(client):
    """GET /api/v1/orders returns 401 JSON when unauthenticated."""
    resp = client.get("/api/v1/orders?page=1&per_page=5")
    assert resp.status_code == 401
    data = resp.get_json()
    assert data is not None
    assert "error" in data
    assert "trace_id" in data


def test_api_auth_me_requires_auth(client):
    """GET /api/v1/auth/me returns 401 JSON when unauthenticated."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    data = resp.get_json()
    assert data is not None
    assert "error" in data
    assert "trace_id" in data


def test_static_file_not_found_returns_404(client):
    """GET /static/nonexistent.js returns 404, not 500."""
    resp = client.get("/static/js/nonexistent_file_xyz.js")
    assert resp.status_code == 404
