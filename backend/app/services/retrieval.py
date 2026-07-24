from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import DocumentChunk


async def secure_retrieve(
    session: AsyncSession,
    query_embedding: list[float],
    user_roles: list[str],
    user_groups: list[str],
    top_k: int | None = None,
) -> list[DocumentChunk]:
    """
    "Need-to-know" retrieval — the core security guarantee of NexusMind.

    This is a HARD PRE-FILTER, not a post-filter: the WHERE clause runs
    before cosine similarity is computed, so a chunk the user isn't
    entitled to is never scored, never ranked, and never has a chance to
    leak into the top-K — regardless of how semantically relevant it is to
    the query. Nothing the LLM prompt says can undo this, because the LLM
    never sees the excluded rows in the first place.

    Access rule: allowed_roles INTERSECTS user_roles OR allowed_groups
    INTERSECTS user_groups. Postgres ARRAY overlap (&&) implements the
    "INTERSECTS" semantics from the brief; SQLAlchemy's `.overlap()`
    comparator compiles directly to that operator.

    Ranking: among only the eligible rows, order by cosine distance
    (pgvector's `<=>` operator, exposed here as `.cosine_distance()`) and
    take the closest `top_k`.
    """
    k = top_k or settings.retrieval_top_k

    stmt = (
        select(DocumentChunk)
        .where(
            or_(
                DocumentChunk.allowed_roles.overlap(user_roles),
                DocumentChunk.allowed_groups.overlap(user_groups),
            )
        )
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(k)
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def cosine_similarity_scores(
    session: AsyncSession,
    chunks: list[DocumentChunk],
    query_embedding: list[float],
) -> list[float]:
    """Re-derive similarity (1 - cosine_distance) per chunk, for the UI's
    confidence score. Cheap in Python since we already have both vectors —
    avoids a second DB round trip."""
    import numpy as np

    q = np.array(query_embedding)
    q_norm = q / (np.linalg.norm(q) or 1.0)

    scores = []
    for chunk in chunks:
        v = np.array(chunk.embedding)
        v_norm = v / (np.linalg.norm(v) or 1.0)
        scores.append(float(np.dot(q_norm, v_norm)))
    return scores
