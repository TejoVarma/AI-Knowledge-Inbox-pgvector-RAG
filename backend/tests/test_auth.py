from sqlalchemy import select

from app.core.security import verify_password
from app.db.database import SessionLocal
from app.db.models import User


def register(client, email="tejo@example.com", password="correct-horse-9"):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_creates_user(client):
    resp = register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "tejo@example.com"
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


def test_invalid_email_rejected(client):
    assert register(client, email="not-an-email").status_code == 422
