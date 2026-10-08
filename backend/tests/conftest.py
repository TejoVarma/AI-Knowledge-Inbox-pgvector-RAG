import os
from pathlib import Path

# must run before any app import - settings and the engine read these at import time
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres:dev@localhost:5433/inbox_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-not-used-anywhere-real")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.db.database import engine  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
FAKE_VECTOR = [0.1] * 1536


def _create_test_database_if_missing(url: str) -> None:
    db_name = make_url(url).database
    admin = create_engine(make_url(url).set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": db_name})
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def test_database():
    # the cleanup below truncates tables, so refuse to run against anything that isn't a test db
    if not make_url(TEST_DATABASE_URL).database.endswith("_test"):
        pytest.exit(f"refusing to run tests against non-test database: {TEST_DATABASE_URL}")

    _create_test_database_if_missing(TEST_DATABASE_URL)

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users, items, chunks CASCADE"))


def _logged_in_client(email: str) -> TestClient:
    c = TestClient(app)
    credentials = {"email": email, "password": "long-enough-pw"}
    c.post("/auth/register", json=credentials)
    token = c.post("/auth/login", json=credentials).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    return c


@pytest.fixture()
def client():
    return _logged_in_client("owner@example.com")


@pytest.fixture()
def other_client():
    return _logged_in_client("intruder@example.com")


@pytest.fixture()
def anon_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_external_calls(monkeypatch):
    # every chunk and every question get the SAME vector, so any saved chunk is a
    # perfect cosine match (distance 0) - keeps retrieval tests deterministic
    monkeypatch.setattr(
        "app.services.ingestion.embed_texts", lambda pieces: [FAKE_VECTOR for _ in pieces]
    )
    monkeypatch.setattr("app.services.retrieval.embed_text", lambda question: FAKE_VECTOR)
    monkeypatch.setattr(
        "app.services.ingestion.generate_suggested_question", lambda content: "mocked question?"
    )
    monkeypatch.setattr(
        "app.services.ingestion.fetch_url_text", lambda url: "mocked fetched page content"
    )

    def fake_generate_answer(question, chunks):
        if not chunks:
            return "I don't have any saved content to answer that yet — add some notes or URLs first."
        return "mocked answer [1]."

    monkeypatch.setattr("app.api.query.generate_answer", fake_generate_answer)
