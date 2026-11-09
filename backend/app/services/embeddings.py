from app.core.config import settings
from app.services.openai_client import client


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = client.embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
