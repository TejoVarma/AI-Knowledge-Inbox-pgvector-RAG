from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.db.models import Chunk, Item
from app.services.embeddings import embed_text


@dataclass
class RetrievedChunk:
    chunk: Chunk
    item: Item
    similarity: float


def retrieve_top_chunks(db: Session, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    k = top_k or settings.top_k_chunks

    if db.scalar(select(Chunk.id).limit(1)) is None:
        return []

    question_vector = embed_text(question)
    distance = Chunk.embedding.cosine_distance(question_vector).label("distance")

    rows = db.execute(
        select(Chunk, distance)
        .options(joinedload(Chunk.item))
        .order_by(distance)
        .limit(k)
    ).all()

    # pgvector gives cosine distance, our threshold is a similarity
    results = [RetrievedChunk(chunk=c, item=c.item, similarity=1 - d) for c, d in rows]
    return [r for r in results if r.similarity >= settings.min_similarity]
