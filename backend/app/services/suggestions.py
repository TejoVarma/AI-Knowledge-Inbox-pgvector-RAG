from app.core.config import settings
from app.core.logging import get_logger
from app.services.openai_client import client

# optional extra, so it gets less patience: a slow suggestion shouldn't hold up a save
_suggestion_client = client.with_options(timeout=8, max_retries=0)
logger = get_logger(__name__)

SUGGESTION_PROMPT = (
    "Generate one short question (under 8 words) a user might ask about the "
    "following saved content. Return ONLY the question, no quotes, no extra text."
)


def generate_suggested_question(content: str) -> str | None:
    try:
        response = _suggestion_client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {"role": "system", "content": SUGGESTION_PROMPT},
                {"role": "user", "content": content[:2000]},
            ],
            temperature=0.7,
            max_tokens=20,
        )
        question = response.choices[0].message.content
        return question.strip() if question else None
    except Exception:
        logger.exception("failed to generate suggested question")
        return None
