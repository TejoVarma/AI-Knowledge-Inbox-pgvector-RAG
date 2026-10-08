import pytest

from app.services.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("", chunk_size=100, overlap=10) == []
    assert chunk_text("   ", chunk_size=100, overlap=10) == []


def test_short_text_returns_single_chunk():
    text = "short note"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks == [text]


def test_long_text_splits_into_multiple_chunks():
    text = "a" * 250
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_overlap_preserves_boundary_content():
    text = "The migration deadline is end of quarter and applies to all embedding models in production."
    chunks = chunk_text(text, chunk_size=40, overlap=15)
    assert len(chunks) >= 2
    tail_of_first = chunks[0][-10:]
    assert tail_of_first in chunks[1]


def test_chunk_size_must_exceed_overlap():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=50, overlap=50)
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=50, overlap=60)
