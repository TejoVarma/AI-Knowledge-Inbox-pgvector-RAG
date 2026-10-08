import pytest
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import Item, User


def save_note(c, content="owner's private note about the goa offsite"):
    return c.post("/ingest", json={"source_type": "note", "content": content})


@pytest.mark.parametrize(
    "method, path, body",
    [
        ("post", "/ingest", {"source_type": "note", "content": "hello"}),
        ("get", "/items", None),
        ("post", "/query", {"question": "anything?"}),
        ("delete", "/items/00000000-0000-0000-0000-000000000000", None),
    ],
)
def test_notes_routes_require_login(anon_client, method, path, body):
    resp = getattr(anon_client, method)(path, **({"json": body} if body else {}))
    assert resp.status_code == 401


def test_users_only_list_their_own_items(client, other_client):
    save_note(client)

    assert len(client.get("/items").json()) == 1
    assert other_client.get("/items").json() == []


def test_search_never_returns_another_users_note(client, other_client):
    # the intruder needs a note of their own, otherwise search returns early on
    # "you have no chunks" and the user filter in the main query never runs
    save_note(client)
    intruder_item_id = save_note(other_client, content="intruder's own note").json()["id"]

    resp = other_client.post("/query", json={"question": "what's happening at the goa offsite?"})
    assert resp.status_code == 200
    assert [s["item_id"] for s in resp.json()["sources"]] == [intruder_item_id]


def test_search_with_empty_inbox_finds_nothing(client, other_client):
    save_note(client)
    assert other_client.post("/query", json={"question": "goa?"}).json()["sources"] == []


def test_search_finds_own_note_even_when_others_have_many(client, other_client):
    # behaviour check only - at this size postgres scans the table instead of using
    # the hnsw index, so this doesn't exercise hnsw.iterative_scan itself
    for i in range(30):
        save_note(other_client, content=f"someone else's note number {i}")
    item_id = save_note(client).json()["id"]

    sources = client.post("/query", json={"question": "goa?"}).json()["sources"]
    assert [s["item_id"] for s in sources] == [item_id]


def test_cannot_delete_another_users_item(client, other_client):
    item_id = save_note(client).json()["id"]

    resp = other_client.delete(f"/items/{item_id}")
    assert resp.status_code == 404  # not 403 - don't confirm it exists

    with SessionLocal() as db:
        assert db.scalar(select(Item).where(Item.id == item_id)) is not None


def test_same_url_allowed_for_different_users(client, other_client):
    url = {"source_type": "url", "url": "https://example.com/shared"}
    assert client.post("/ingest", json=url).status_code == 201
    assert other_client.post("/ingest", json=url).status_code == 201
    assert client.post("/ingest", json=url).status_code == 409


def test_deleting_a_user_deletes_their_items(client):
    save_note(client)
    with SessionLocal() as db:
        db.delete(db.scalar(select(User).where(User.email == "owner@example.com")))
        db.commit()
        assert db.scalars(select(Item)).all() == []
