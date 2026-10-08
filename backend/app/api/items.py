import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import Item, SourceType
from app.schemas.items import IngestRequest, ItemResponse
from app.services import ingestion
from app.services.url_fetcher import UrlFetchError

router = APIRouter()
logger = get_logger(__name__)


@router.post("/ingest", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def ingest_item(payload: IngestRequest, db: Session = Depends(get_db)) -> ItemResponse:
    try:
        if payload.source_type == SourceType.note:
            item = ingestion.ingest_note(db, content=payload.content)  # type: ignore[arg-type]
        else:
            item = ingestion.ingest_url(db, url=payload.url)  # type: ignore[arg-type]
    except UrlFetchError as exc:
        db.rollback()
        logger.warning("url ingestion failed", extra={"extra_fields": {"url": payload.url, "error": str(exc)}})
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        logger.info("duplicate url ingestion rejected", extra={"extra_fields": {"url": payload.url}})
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="this url has already been saved"
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("ingestion failed unexpectedly")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="failed to process content") from exc

    return _to_response(item)


@router.get("/items", response_model=list[ItemResponse])
def list_items(db: Session = Depends(get_db)) -> list[ItemResponse]:
    items = db.query(Item).order_by(Item.created_at.desc()).all()
    return [_to_response(item) for item in items]


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")

    db.delete(item)
    db.commit()
    logger.info("item deleted", extra={"extra_fields": {"item_id": item_id}})


def _to_response(item: Item) -> ItemResponse:
    return ItemResponse(
        id=item.id,
        source_type=item.source_type,
        source_ref=item.source_ref,
        content=item.content,
        suggested_question=item.suggested_question,
        created_at=item.created_at,
        chunk_count=len(item.chunks),
    )
