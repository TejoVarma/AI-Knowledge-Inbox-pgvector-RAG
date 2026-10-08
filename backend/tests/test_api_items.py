import uuid

from app.services.url_fetcher import UrlFetchError


def test_ingest_note_success(client):
    resp = client.post("/ingest", json={"source_type": "note", "content": "test note content"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["source_type"] == "note"
    assert data["content"] == "test note content"
    assert data["chunk_count"] >= 1


def test_ingest_note_empty_content_rejected(client):
    resp = client.post("/ingest", json={"source_type": "note", "content": ""})
    assert resp.status_code == 422


def test_ingest_url_success(client):
    resp = client.post("/ingest", json={"source_type": "url", "url": "https://example.com/page"})
    assert resp.status_code == 201
    assert resp.json()["source_ref"] == "https://example.com/page"


def test_ingest_duplicate_url_rejected(client):
    first = client.post("/ingest", json={"source_type": "url", "url": "https://example.com/dup"})
    assert first.status_code == 201
    second = client.post("/ingest", json={"source_type": "url", "url": "https://example.com/dup"})
    assert second.status_code == 409


def test_ingest_url_fetch_failure_returns_422(client, monkeypatch):
    def raise_fetch_error(url):
        raise UrlFetchError("failed to fetch url: mocked failure")

    monkeypatch.setattr("app.services.ingestion.fetch_url_text", raise_fetch_error)
    resp = client.post("/ingest", json={"source_type": "url", "url": "https://example.com/broken"})
    assert resp.status_code == 422


def test_list_items_returns_saved_items_newest_first(client):
    client.post("/ingest", json={"source_type": "note", "content": "first note"})
    client.post("/ingest", json={"source_type": "note", "content": "second note"})

    resp = client.get("/items")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert items[0]["content"] == "second note"


def test_delete_item_then_404_on_second_delete(client):
    created = client.post("/ingest", json={"source_type": "note", "content": "to be deleted"}).json()
    item_id = created["id"]

    delete_resp = client.delete(f"/items/{item_id}")
    assert delete_resp.status_code == 204

    second_delete = client.delete(f"/items/{item_id}")
    assert second_delete.status_code == 404


def test_delete_with_non_uuid_id_rejected(client):
    resp = client.delete("/items/2")
    assert resp.status_code == 422


def test_delete_unknown_uuid_returns_404(client):
    resp = client.delete(f"/items/{uuid.uuid4()}")
    assert resp.status_code == 404
