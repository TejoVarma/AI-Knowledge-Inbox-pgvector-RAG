from openai import OpenAI

from app.core.config import settings
from app.services.retrieval import RetrievedChunk

_client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = (
    "You are a knowledge-base assistant. Answer the user's question using ONLY the "
    "numbered context snippets provided below. Cite the snippet numbers you used, "
    "e.g. '[1]', inline in your answer. If the context does not contain enough "
    "information to answer, say so plainly instead of guessing."
)


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for i, retrieved in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] (source: {retrieved.item.source_type.value} #{retrieved.item.id})\n{retrieved.chunk.text}"
        )
    return "\n\n".join(lines)


def generate_answer(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "I don't have any saved content to answer that yet — add some notes or URLs first."

    context_block = build_context_block(chunks)
    response = _client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""
