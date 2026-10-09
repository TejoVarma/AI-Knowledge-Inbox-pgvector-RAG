from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, items, query
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="AI Knowledge Inbox")

# empty by default: the frontend calls the api through its own origin, so the browser
# never needs cross-origin access. "*" would be meaningless with cookies anyway
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)

app.include_router(auth.router, tags=["auth"])
app.include_router(items.router, tags=["items"])
app.include_router(query.router, tags=["query"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
