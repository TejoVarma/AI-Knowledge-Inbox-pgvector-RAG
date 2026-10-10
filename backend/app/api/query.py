from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import Item, User
from app.schemas.query import QueryRequest, QueryResponse, SourceSnippet
from app.services.answering import generate_answer
from app.services.retrieval import retrieve_top_chunks

router = APIRouter()
logger = get_logger(__name__)

EMPTY_INBOX_ANSWER = "I don't have any saved content to answer that yet — add some notes or URLs first."
NOTHING_RELEVANT_ANSWER = "I couldn't find anything in your saved items about that."


@router.post("/query", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    try:
        top_chunks = retrieve_top_chunks(db, payload.question, current_user.id)
        if top_chunks:
            answer = generate_answer(payload.question, top_chunks)
        else:
            # "you have nothing saved" and "nothing you saved matches" need different answers
            has_items = db.scalar(select(Item.id).where(Item.user_id == current_user.id).limit(1))
            answer = NOTHING_RELEVANT_ANSWER if has_items else EMPTY_INBOX_ANSWER
    except Exception as exc:
        logger.exception("query failed unexpectedly")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="failed to answer question") from exc

    logger.info(
        "query answered",
        extra={"extra_fields": {"question_len": len(payload.question), "chunks_used": len(top_chunks)}},
    )

    return QueryResponse(
        answer=answer,
        sources=[
            SourceSnippet(
                item_id=r.item.id,
                source_type=r.item.source_type.value,
                source_ref=r.item.source_ref,
                chunk_text=r.chunk.text,
                similarity=round(r.similarity, 4),
            )
            for r in top_chunks
        ],
    )
