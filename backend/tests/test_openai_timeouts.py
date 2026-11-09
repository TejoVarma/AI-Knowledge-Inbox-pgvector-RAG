import httpx
import openai

from app.services import openai_client, suggestions


def _timeout_error(*args, **kwargs):
    raise openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com/v1/embeddings"))


def test_calls_give_up_instead_of_waiting_ten_minutes():
    assert openai_client.client.timeout == 15
    assert openai_client.client.max_retries == 1
    # the suggestion is optional, so it gets less patience than the main work
    assert suggestions._suggestion_client.timeout == 8
    assert suggestions._suggestion_client.max_retries == 0


def test_query_timeout_returns_504_with_a_clear_message(client, monkeypatch):
    client.post("/ingest", json={"source_type": "note", "content": "something saved"})
    monkeypatch.setattr("app.api.query.generate_answer", _timeout_error)

    response = client.post("/query", json={"question": "what did I save?"})

    assert response.status_code == 504
    assert "took too long" in response.json()["detail"]


def test_ingest_timeout_returns_504_and_saves_nothing(client, monkeypatch):
    monkeypatch.setattr("app.services.ingestion.embed_texts", _timeout_error)

    response = client.post("/ingest", json={"source_type": "note", "content": "a note"})

    assert response.status_code == 504
    assert "took too long" in response.json()["detail"]
    assert client.get("/items").json() == []
