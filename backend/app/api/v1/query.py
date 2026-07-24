from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserContext, get_current_user
from app.db.database import get_session
from app.schemas.query import QueryRequest, QueryResponse, SourceCitation
from app.services.embeddings import get_embedding
from app.services.llm import generate_answer
from app.services.retrieval import cosine_similarity_scores, secure_retrieve

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    body: QueryRequest,
    user: UserContext = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> QueryResponse:
    """
    1. Identity comes ONLY from the verified JWT (never from the request body).
    2. Embed the query.
    3. Hard-gate pre-filter + cosine similarity search (see services/retrieval.py).
    4. Generate the answer strictly from the eligible context.
    """
    query_embedding = await get_embedding(body.query)

    chunks = await secure_retrieve(
        session=session,
        query_embedding=query_embedding,
        user_roles=user.roles,
        user_groups=user.groups,
    )

    answer = await generate_answer(body.query, chunks)

    scores = await cosine_similarity_scores(session, chunks, query_embedding)
    confidence = round(sum(scores) / len(scores), 3) if scores else 0.0

    return QueryResponse(
        answer=answer,
        sources=[
            SourceCitation(
                title=c.title,
                source_type=c.source_type,
                source_url=c.source_url,
                author=c.author,
            )
            for c in chunks
        ],
        confidence=confidence,
        access_denied=len(chunks) == 0,
    )
