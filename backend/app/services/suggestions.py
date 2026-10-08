from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger

_client = OpenAI(api_key=settings.openai_api_key)
logger = get_logger(__name__)

SUGGESTION_PROMPT = (
    "Generate one short question (under 8 words) a user might ask about the "
    "following saved content. Return ONLY the question, no quotes, no extra text."
)


def generate_suggested_question(content: str) -> str | None:
    try:
        response = _client.chat.completions.create(
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
