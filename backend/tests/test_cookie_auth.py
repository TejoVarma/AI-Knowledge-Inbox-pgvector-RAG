import uuid
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.security import create_access_token


def set_cookie_headers(resp) -> dict[str, str]:
    # {"access_token": "access_token=...; HttpOnly; Max-Age=...", ...}
    return {h.split("=", 1)[0]: h for h in resp.headers.get_list("set-cookie")}


def csrf_header(c):
    return {"X-CSRF-Token": c.cookies["csrf_token"]}


def test_login_sets_both_cookies_with_safe_flags(anon_client):
    credentials = {"email": "flags@example.com", "password": "long-enough-pw"}
    anon_client.post("/auth/register", json=credentials)
    resp = anon_client.post("/auth/login", json=credentials)

    assert resp.status_code == 200
    cookies = set_cookie_headers(resp)
    access, csrf = cookies["access_token"].lower(), cookies["csrf_token"].lower()

    assert "httponly" in access
    assert "httponly" not in csrf  # the frontend has to read this one
    for header in (access, csrf):
        assert "secure" in header
        assert "samesite=lax" in header
        assert "path=/" in header
        assert f"max-age={settings.jwt_expire_minutes * 60}" in header


def test_session_lasts_one_day():
    assert settings.jwt_expire_minutes * 60 == 86400


def test_login_body_never_contains_the_token(anon_client):
    credentials = {"email": "body@example.com", "password": "long-enough-pw"}
    anon_client.post("/auth/register", json=credentials)
    data = anon_client.post("/auth/login", json=credentials).json()

    assert data["email"] == "body@example.com"
    assert "access_token" not in data
    assert anon_client.cookies["access_token"] not in str(data)


def test_cookie_alone_authenticates_safe_requests(browser_client):
    assert browser_client.get("/auth/me").json()["email"] == "browser@example.com"
    assert browser_client.get("/items").status_code == 200


def test_cookie_post_without_csrf_header_is_rejected(browser_client):
    resp = browser_client.post("/ingest", json={"source_type": "note", "content": "hello"})
    assert resp.status_code == 403
    assert resp.json() == {"detail": "csrf check failed"}


def test_cookie_post_with_wrong_csrf_header_is_rejected(browser_client):
    resp = browser_client.post(
        "/ingest",
        json={"source_type": "note", "content": "hello"},
        headers={"X-CSRF-Token": "guessed-value"},
    )
    assert resp.status_code == 403


def test_cookie_post_with_matching_csrf_header_works(browser_client):
    resp = browser_client.post(
        "/ingest", json={"source_type": "note", "content": "hello"}, headers=csrf_header(browser_client)
    )
    assert resp.status_code == 201


def test_cookie_delete_needs_csrf_too(browser_client):
    item_id = browser_client.post(
        "/ingest", json={"source_type": "note", "content": "hello"}, headers=csrf_header(browser_client)
    ).json()["id"]

    assert browser_client.delete(f"/items/{item_id}").status_code == 403
    assert browser_client.delete(f"/items/{item_id}", headers=csrf_header(browser_client)).status_code == 204


def test_bearer_requests_skip_the_csrf_check(client):
    # `client` authenticates with the Authorization header and has no cookies at all
    resp = client.post("/ingest", json={"source_type": "note", "content": "hello"})
    assert resp.status_code == 201


def test_logout_clears_cookies_and_ends_the_session(browser_client):
    resp = browser_client.post("/auth/logout")
    assert resp.status_code == 204

    cookies = set_cookie_headers(resp)
    assert 'max-age=0' in cookies["access_token"].lower()
    assert 'max-age=0' in cookies["csrf_token"].lower()
    assert "access_token" not in browser_client.cookies
    assert browser_client.get("/auth/me").status_code == 401


def test_expired_cookie_token_is_rejected(browser_client):
    user_id = uuid.UUID(browser_client.get("/auth/me").json()["id"])
    browser_client.cookies.set(
        "access_token", create_access_token(user_id, expires_in=timedelta(minutes=-1)), domain="testserver.local"
    )
    assert browser_client.get("/auth/me").status_code == 401


def test_cors_does_not_allow_other_origins(browser_client):
    resp = browser_client.get("/auth/me", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in resp.headers


def test_token_endpoint_caps_password_length(anon_client):
    resp = anon_client.post("/auth/token", data={"username": "x@example.com", "password": "a" * 129})
    assert resp.status_code == 422


def test_wildcard_cors_origin_is_refused():
    with pytest.raises(ValidationError):
        Settings(cors_origins=["*"])
    assert Settings(cors_origins=["https://app.example"]).cors_origins == ["https://app.example"]
