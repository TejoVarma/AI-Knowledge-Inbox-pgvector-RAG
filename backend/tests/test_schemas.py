import pytest
from pydantic import ValidationError

from app.schemas.items import IngestRequest
from app.schemas.query import QueryRequest


def test_note_requires_content():
    with pytest.raises(ValidationError):
        IngestRequest(source_type="note", content=None)
    with pytest.raises(ValidationError):
        IngestRequest(source_type="note", content="   ")


def test_url_requires_url():
    with pytest.raises(ValidationError):
        IngestRequest(source_type="url", url=None)
    with pytest.raises(ValidationError):
        IngestRequest(source_type="url", url="   ")


def test_valid_note_passes():
    req = IngestRequest(source_type="note", content="a real note")
    assert req.content == "a real note"


def test_valid_url_passes():
    req = IngestRequest(source_type="url", url="https://example.com")
    assert req.url == "https://example.com"


def test_whitespace_is_stripped():
    req = IngestRequest(source_type="note", content="  padded note  ")
    assert req.content == "padded note"

    req = IngestRequest(source_type="url", url="  https://example.com  ")
    assert req.url == "https://example.com"


def test_question_cannot_be_empty():
    with pytest.raises(ValidationError):
        QueryRequest(question="")


def test_question_within_length_limit_passes():
    req = QueryRequest(question="what did I save about pricing?")
    assert req.question == "what did I save about pricing?"


def test_question_over_length_limit_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(question="a" * 2001)
