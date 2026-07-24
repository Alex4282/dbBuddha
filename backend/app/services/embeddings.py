import httpx
from openai import AsyncOpenAI

from app.core.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def _ollama_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Ollama's /api/embeddings endpoint embeds one prompt per call."""
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=60) as client:
        vectors = []
        for text in texts:
            response = await client.post(
                "/api/embeddings", json={"model": settings.embedding_model, "prompt": text}
            )
            response.raise_for_status()
            vectors.append(response.json()["embedding"])
        return vectors


async def get_embedding(text: str) -> list[float]:
    """Embed a single string with the configured embedding model.

    Used identically at ingestion time (seed_data.py) and query time
    (api/v1/query.py) so vectors live in the same space.
    """
    if settings.embedding_provider == "ollama":
        return (await _ollama_embeddings_batch([text]))[0]
    response = await _client.embeddings.create(model=settings.embedding_model, input=text)
    return response.data[0].embedding


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Batch variant for ingestion — one API round trip for many chunks (OpenAI only)."""
    if settings.embedding_provider == "ollama":
        return await _ollama_embeddings_batch(texts)
    response = await _client.embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]
