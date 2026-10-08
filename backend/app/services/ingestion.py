import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import Chunk, Item, SourceType
from app.services.chunking import chunk_text
from app.services.embeddings import embed_texts
from app.services.suggestions import generate_suggested_question
from app.services.url_fetcher import fetch_url_text

logger = get_logger(__name__)


def ingest_note(db: Session, user_id: uuid.UUID, content: str) -> Item:
    return _ingest(db, user_id, source_type=SourceType.note, content=content.strip(), source_ref=None)


def ingest_url(db: Session, user_id: uuid.UUID, url: str) -> Item:
    content = fetch_url_text(url)
    return _ingest(db, user_id, source_type=SourceType.url, content=content, source_ref=url)


def _ingest(
    db: Session, user_id: uuid.UUID, source_type: SourceType, content: str, source_ref: str | None
) -> Item:
    item = Item(
        user_id=user_id,
        source_type=source_type,
        content=content,
        source_ref=source_ref,
        suggested_question=generate_suggested_question(content),
    )
    db.add(item)
    db.flush()

    pieces = chunk_text(content, settings.chunk_size_chars, settings.chunk_overlap_chars)
    if pieces:
        vectors = embed_texts(pieces)
        for index, (piece, vector) in enumerate(zip(pieces, vectors)):
            db.add(
                Chunk(
                    item_id=item.id,
                    chunk_index=index,
                    text=piece,
                    embedding=vector,
                )
            )

    db.commit()
    db.refresh(item)

    logger.info(
        "item ingested",
        extra={
            "extra_fields": {
                "item_id": str(item.id),
                "user_id": str(user_id),
                "source_type": source_type.value,
                "chunk_count": len(pieces),
            }
        },
    )
    return item
