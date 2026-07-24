import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.database import Base

EMBEDDING_DIM = settings.embedding_dim


class DocumentChunk(Base):
    """One retrievable chunk of ingested knowledge (Jira / Confluence / Teams / GitHub).

    `allowed_roles` / `allowed_groups` are the ACL payload that makes the
    "need-to-know" hard-gate possible: the pre-filter in
    services/retrieval.py only ever considers rows where at least one of
    these arrays overlaps the requesting user's roles/groups. No row that
    fails that check is ever passed to the similarity search or the LLM.
    """

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(50))  # "Jira" | "Confluence" | "Teams" | "GitHub"
    source_url: Mapped[str] = mapped_column(String(1000))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))

    allowed_roles: Mapped[list[str]] = mapped_column(ARRAY(String))
    allowed_groups: Mapped[list[str]] = mapped_column(ARRAY(String))

    # Extension beyond the base spec: powers the "Live SME Widget" (STEP 4),
    # which surfaces who authored/owns each piece of knowledge.
    author: Mapped[str] = mapped_column(String(200), default="unknown")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    # Stable identity for upsert-on-resync (e.g. "github:owner/repo:blob:path",
    # "github:owner/repo:issue:42"). NULL for hand-seeded demo rows, which are
    # never re-synced.
    external_id: Mapped[str | None] = mapped_column(String(500), unique=True, nullable=True)
