import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session, contains_eager

from app.core.config import settings
from app.db.models import Chunk, Item
from app.services.embeddings import embed_text


@dataclass
class RetrievedChunk:
    chunk: Chunk
    item: Item
    similarity: float


def retrieve_top_chunks(
    db: Session, question: str, user_id: uuid.UUID, top_k: int | None = None
) -> list[RetrievedChunk]:
    k = top_k or settings.top_k_chunks

    has_chunks = db.scalar(
        select(Chunk.id).join(Chunk.item).where(Item.user_id == user_id).limit(1)
    )
    if has_chunks is None:
        return []

    question_vector = embed_text(question)
    distance = Chunk.embedding.cosine_distance(question_vector).label("distance")

    # hnsw finds the nearest chunks across ALL users first and filters after, so a user
    # with few chunks could get nothing back - iterative scan keeps going until it has k
    db.execute(text("SET LOCAL hnsw.iterative_scan = strict_order"))

    rows = db.execute(
        select(Chunk, distance)
        .join(Chunk.item)
        .where(Item.user_id == user_id)
        .options(contains_eager(Chunk.item))
        .order_by(distance)
        .limit(k)
    ).all()

    # pgvector gives cosine distance, our threshold is a similarity
    results = [RetrievedChunk(chunk=c, item=c.item, similarity=1 - d) for c, d in rows]
    return [r for r in results if r.similarity >= settings.min_similarity]
