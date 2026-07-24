from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.core.security import DEMO_PERSONAS, create_access_token
from app.db.database import AsyncSessionLocal
from app.db.models import DocumentChunk
from app.schemas.query import SMEEntry

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.post("/auth/mock-token")
async def mock_token(persona: str) -> dict:
    """
    Demo-only identity issuer powering the hackathon Persona Switcher.

    Real deployments delete this file and point `oauth2_scheme` at
    Auth0 / NextAuth's JWKS endpoint instead — the rest of the backend
    (security.py, retrieval.py) doesn't change, because it only ever reads
    `roles` / `groups` off a verified token.
    """
    user = DEMO_PERSONAS.get(persona)
    if user is None:
        raise HTTPException(status_code=404, detail=f"Unknown persona '{persona}'. Try: {list(DEMO_PERSONAS)}")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user.model_dump(),
    }


@router.get("/sme", response_model=list[SMEEntry])
async def sme_directory() -> list[SMEEntry]:
    """Powers the 'Live SME Widget' — who knows what, based on author metadata.

    Intentionally unauthenticated / unfiltered: this surfaces *who to ask*,
    not the sensitive content itself, so it's safe to show every new hire.
    """
    async with AsyncSessionLocal() as session:
        stmt = select(
            DocumentChunk.author,
            func.array_agg(func.distinct(DocumentChunk.source_type)).label("domains"),
            func.count(DocumentChunk.id).label("document_count"),
        ).group_by(DocumentChunk.author)
        rows = (await session.execute(stmt)).all()

    return [
        SMEEntry(author=row.author, domains=row.domains, document_count=row.document_count)
        for row in rows
    ]
