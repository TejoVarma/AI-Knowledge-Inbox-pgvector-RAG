import json
import uuid
from datetime import timedelta

import jwt
import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, verify_password
from app.db.database import SessionLocal
from app.db.models import User


# auth tests register and log in by hand, so they start from a client with no token
@pytest.fixture()
def client(anon_client):
    return anon_client


def register(client, email="tejo@example.com", password="correct-horse-9", name="Tejo"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def test_register_creates_user(client):
    resp = register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "tejo@example.com"
    assert data["name"] == "Tejo"
    assert "id" in data and "created_at" in data


def test_register_never_returns_password_or_hash(client):
    data = register(client).json()
    assert "password" not in data
    assert "password_hash" not in data


def test_password_is_stored_hashed_not_plain(client):
    register(client, password="correct-horse-9")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == "tejo@example.com"))

    assert user.password_hash != "correct-horse-9"
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password("correct-horse-9", user.password_hash)
    assert not verify_password("wrong-password", user.password_hash)


def test_email_is_normalized_to_lowercase(client):
    resp = register(client, email="  Tejo@Example.COM ")
    assert resp.status_code == 201
    assert resp.json()["email"] == "tejo@example.com"


def test_duplicate_email_rejected(client):
    assert register(client).status_code == 201
    assert register(client, email="TEJO@example.com").status_code == 409


def test_short_password_rejected(client):
    assert register(client, password="short").status_code == 422


def test_name_is_required(client):
    resp = client.post("/auth/register", json={"email": "tejo@example.com", "password": "correct-horse-9"})
    assert resp.status_code == 422


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_blank_or_too_long_name_rejected(client, name):
    assert register(client, name=name).status_code == 422


def test_database_refuses_a_user_without_a_name():
    # the api checks the name, but the column itself must too - nothing else can slip one in
    with SessionLocal() as db:
        db.add(User(email="nameless@example.com", password_hash="x"))
        with pytest.raises(IntegrityError):
            db.commit()


def test_name_is_trimmed(client):
    assert register(client, name="  Tejo Varma  ").json()["name"] == "Tejo Varma"


def test_invalid_email_rejected(client):
    assert register(client, email="not-an-email").status_code == 422


def login(client, email="tejo@example.com", password="correct-horse-9"):
    return client.post("/auth/login", json={"email": email, "password": password})


def get_token(client, email="tejo@example.com", password="correct-horse-9"):
    return client.post("/auth/token", data={"username": email, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_token_endpoint_returns_bearer_token(client):
    register(client)
    resp = get_token(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"].count(".") == 2  # header.payload.signature


def test_login_email_is_case_insensitive_on_both_paths(client):
    register(client)
    assert login(client, email="TEJO@Example.com").status_code == 200
    assert get_token(client, email="TEJO@Example.com").status_code == 200


@pytest.mark.parametrize("attempt", [login, get_token])
def test_wrong_password_and_unknown_email_look_identical(client, attempt):
    register(client)
    wrong_password = attempt(client, password="not-my-password")
    unknown_email = attempt(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {"detail": "invalid email or password"}


def test_me_returns_current_user(client):
    register(client)
    token = get_token(client).json()["access_token"]

    resp = client.get("/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "tejo@example.com"
    assert resp.json()["name"] == "Tejo"


def test_me_without_token_is_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"


def test_me_with_garbage_token_is_401(client):
    assert client.get("/auth/me", headers=auth_header("not.a.token")).status_code == 401


def test_tampered_token_is_rejected(client):
    # swap in another user's id in the payload but keep the original signature
    register(client)
    token = get_token(client).json()["access_token"]
    header, _, signature = token.split(".")
    other_user_payload = jwt.utils.base64url_encode(
        json.dumps({"sub": str(uuid.uuid4()), "exp": 9999999999}).encode()
    ).decode()

    forged = f"{header}.{other_user_payload}.{signature}"
    assert client.get("/auth/me", headers=auth_header(forged)).status_code == 401


def test_token_signed_with_another_secret_is_rejected(client):
    register(client)
    user_id = client.get(
        "/auth/me", headers=auth_header(get_token(client).json()["access_token"])
    ).json()["id"]
    forged = jwt.encode({"sub": user_id, "exp": 9999999999}, "attacker-secret", algorithm="HS256")
    assert client.get("/auth/me", headers=auth_header(forged)).status_code == 401


def test_expired_token_is_rejected(client):
    register(client)
    user_id = uuid.UUID(
        client.get("/auth/me", headers=auth_header(get_token(client).json()["access_token"])).json()["id"]
    )
    expired = create_access_token(user_id, expires_in=timedelta(minutes=-1))
    assert client.get("/auth/me", headers=auth_header(expired)).status_code == 401


def test_token_for_deleted_user_is_rejected(client):
    register(client)
    token = get_token(client).json()["access_token"]
    with SessionLocal() as db:
        db.execute(delete(User))
        db.commit()
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401
