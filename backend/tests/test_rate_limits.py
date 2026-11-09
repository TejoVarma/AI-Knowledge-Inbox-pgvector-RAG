import pytest

from app.core.config import settings


def _save_note(client, text="a note"):
    return client.post("/ingest", json={"source_type": "note", "content": text})


def _ask(client):
    return client.post("/query", json={"question": "what did I save?"})


def test_query_is_limited_per_user(client, other_client, monkeypatch):
    monkeypatch.setattr(settings, "query_rate_limit", "2 per hour")

    assert _ask(client).status_code == 200
    assert _ask(client).status_code == 200
    blocked = _ask(client)

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0
    # one user hitting the limit must not lock anyone else out
    assert _ask(other_client).status_code == 200


def test_ingest_is_limited_per_user(client, other_client, monkeypatch):
    monkeypatch.setattr(settings, "ingest_rate_limit", "2 per hour")

    assert _save_note(client, "one").status_code == 201
    assert _save_note(client, "two").status_code == 201
    assert _save_note(client, "three").status_code == 429
    assert _save_note(other_client).status_code == 201


def test_rate_limited_ingest_saves_nothing(client, monkeypatch):
    monkeypatch.setattr(settings, "ingest_rate_limit", "1 per hour")

    _save_note(client, "kept")
    _save_note(client, "rejected")

    assert [item["content"] for item in client.get("/items").json()] == ["kept"]


def test_item_cap_blocks_saving_until_something_is_deleted(client, monkeypatch):
    monkeypatch.setattr(settings, "max_items_per_user", 2)

    first = _save_note(client, "one").json()
    _save_note(client, "two")
    full = _save_note(client, "three")

    assert full.status_code == 403
    assert "2" in full.json()["detail"]

    client.delete(f"/items/{first['id']}")
    assert _save_note(client, "three").status_code == 201


def test_openai_budget_is_shared_by_everyone(client, other_client, monkeypatch):
    monkeypatch.setattr(settings, "openai_daily_limit", "3 per day")

    assert _save_note(client).status_code == 201
    assert _ask(client).status_code == 200
    assert _ask(other_client).status_code == 200

    blocked = _ask(other_client)
    assert blocked.status_code == 429
    assert _save_note(client, "another").status_code == 429


@pytest.mark.parametrize("path", ["/auth/login", "/auth/token"])
def test_login_attempts_are_limited_per_email(path, anon_client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit", "3 per 15 minutes")
    anon_client.post(
        "/auth/register",
        json={"name": "Victim", "email": "victim@example.com", "password": "long-enough-pw"},
    )

    def attempt(email, password):
        if path == "/auth/token":
            return anon_client.post(path, data={"username": email, "password": password})
        return anon_client.post(path, json={"email": email, "password": password})

    for _ in range(3):
        assert attempt("victim@example.com", "wrong-password").status_code == 401

    # even the right password is refused once the limit is hit - otherwise
    # the attacker would learn which guess was correct
    assert attempt("victim@example.com", "long-enough-pw").status_code == 429
    assert attempt("someone-else@example.com", "whatever-pw").status_code == 401


def test_login_and_token_share_one_counter(anon_client, monkeypatch):
    monkeypatch.setattr(settings, "login_rate_limit", "2 per 15 minutes")

    anon_client.post("/auth/login", json={"email": "victim@example.com", "password": "guess-one"})
    anon_client.post("/auth/token", data={"username": "victim@example.com", "password": "guess-two"})

    third = anon_client.post("/auth/login", json={"email": "Victim@Example.com", "password": "guess-three"})
    assert third.status_code == 429


def test_registration_is_limited_app_wide(anon_client, monkeypatch):
    monkeypatch.setattr(settings, "register_rate_limit", "2 per hour")

    def register(n):
        return anon_client.post(
            "/auth/register",
            json={"name": "New User", "email": f"new{n}@example.com", "password": "long-enough-pw"},
        )

    assert register(1).status_code == 201
    assert register(2).status_code == 201
    assert register(3).status_code == 429


def test_token_rejects_oversized_username_before_counting(anon_client):
    # every username tried becomes a key in the in-memory counters, so a huge one must
    # be refused before it is stored
    response = anon_client.post("/auth/token", data={"username": "a" * 300, "password": "whatever-pw"})

    assert response.status_code == 422
