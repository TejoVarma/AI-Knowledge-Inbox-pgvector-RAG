from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import items, query
from app.core.logging import configure_logging, get_logger
from app.db.database import init_db

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="AI Knowledge Inbox")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router, tags=["items"])
app.include_router(query.router, tags=["query"])


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("app startup complete")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
