import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import settings
from app.db.models import DocumentChunk

SYSTEM_PROMPT = """You are NexusMind, an internal engineering onboarding assistant.

Answer the user's query using ONLY the provided context below. The context
has already been security-filtered for this specific user — if something
is not present in it, that means the user is not entitled to see it, not
that it doesn't exist.

If the answer is not present in the context, respond with EXACTLY:
"I do not have access to that information."
Do not speculate, do not soften it, do not explain why.

Otherwise, answer clearly and concisely, and end with a "Sources" section
listing each source you used as a Markdown link: [Title](source_url).
"""

_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
_anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


def _build_context_block(chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return "(no eligible context — the user's role/group grants no access to relevant documents)"
    parts = []
    for c in chunks:
        parts.append(f"### {c.title} ({c.source_type})\nURL: {c.source_url}\n\n{c.content}")
    return "\n\n---\n\n".join(parts)


async def _ollama_generate(user_message: str) -> str:
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120) as client:
        response = await client.post(
            "/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


async def generate_answer(query: str, chunks: list[DocumentChunk]) -> str:
    # Belt-and-suspenders: if the pre-filter returned nothing, never even
    # call the LLM — return the denial deterministically.
    if not chunks:
        return "I do not have access to that information."

    context = _build_context_block(chunks)
    user_message = f"Context:\n{context}\n\nUser question: {query}"

    if settings.llm_provider == "ollama":
        return await _ollama_generate(user_message)

    if settings.llm_provider == "anthropic":
        response = await _anthropic_client.messages.create(
            model=settings.llm_model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    response = await _openai_client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=800,
    )
    return response.choices[0].message.content or ""
