def test_query_with_nothing_saved_returns_fallback_no_sources(client):
    resp = client.post("/query", json={"question": "anything?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["sources"] == []
    assert "don't have any saved content" in data["answer"]


def test_query_rejects_empty_question(client):
    resp = client.post("/query", json={"question": ""})
    assert resp.status_code == 422


def test_save_then_ask_full_flow(client):
    """Save a note, then ask a question about it — the full ingest -> retrieve
    -> answer pipeline, not just each route checked in isolation."""
    ingest_resp = client.post(
        "/ingest",
        json={
            "source_type": "note",
            "content": "Standup notes: migrate embeddings table to text-embedding-3-small.",
        },
    )
    assert ingest_resp.status_code == 201
    saved_item_id = ingest_resp.json()["id"]

    query_resp = client.post("/query", json={"question": "what should we migrate to?"})
    assert query_resp.status_code == 200

    data = query_resp.json()
    assert data["answer"] == "mocked answer [1]."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["item_id"] == saved_item_id
    assert data["sources"][0]["source_type"] == "note"
    assert data["sources"][0]["similarity"] == 1.0  # mocked embeddings are identical vectors


def test_save_url_then_ask_includes_url_source(client):
    client.post("/ingest", json={"source_type": "url", "url": "https://example.com/article"})

    resp = client.post("/query", json={"question": "what's in the article?"})
    assert resp.status_code == 200

    sources = resp.json()["sources"]
    assert len(sources) == 1
    assert sources[0]["source_type"] == "url"
    assert sources[0]["source_ref"] == "https://example.com/article"


def test_unrelated_question_is_filtered_out(client, monkeypatch):
    # saved chunks point one way, the question points the opposite way -> cosine
    # distance 2, similarity -1, far below min_similarity
    client.post("/ingest", json={"source_type": "note", "content": "goa offsite budget"})
    monkeypatch.setattr("app.services.retrieval.embed_text", lambda q: [-0.1] * 1536)

    resp = client.post("/query", json={"question": "how do I bake bread?"})
    assert resp.status_code == 200
    assert resp.json()["sources"] == []
