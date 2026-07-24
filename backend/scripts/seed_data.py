"""
Hackathon-demo-ready ingestion worker.

Parse -> Generate Embeddings -> Attach ACL Tags -> Upsert into Vector DB.

In production this logic lives inside the "Background Workers / Celery Sync
Jobs" that pull from real Confluence / Jira / Teams / GitHub connectors
(see the architecture doc's ETL stage). For the hackathon, the "extraction"
step is replaced with the hard-coded payloads below, so the demo is
reproducible with one command:

    python -m scripts.seed_data
"""

import asyncio

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import DocumentChunk
from app.services.embeddings import get_embeddings_batch

# 1. Public technical docs — visible to dev + management.
PUBLIC_TECHNICAL_DOCS = [
    {
        "title": "How to Deploy the Payment Microservice via Helm",
        "source_type": "Confluence",
        "source_url": "https://confluence.internal/spaces/ENG/payment-helm-deploy",
        "author": "Priya Nair",
        "content": (
            "To deploy the payment microservice: 1) helm repo update, "
            "2) helm upgrade --install payment-svc charts/payment-svc -f values.prod.yaml, "
            "3) verify rollout with kubectl rollout status deploy/payment-svc, "
            "4) check /healthz on the new pods before removing the old ReplicaSet."
        ),
    },
    {
        "title": "Auth Service API Specs",
        "source_type": "Confluence",
        "source_url": "https://confluence.internal/spaces/ENG/auth-service-api-spec",
        "author": "Priya Nair",
        "content": (
            "The Auth Service exposes POST /token (password + refresh grant), "
            "POST /token/revoke, and GET /userinfo. Tokens are JWTs signed with "
            "RS256, 15-minute access token lifetime, 7-day refresh token lifetime. "
            "To run it locally: docker compose up auth-service, then hit "
            "http://localhost:4000/health to confirm it's ready."
        ),
    },
]

# 2. Sensitive managerial data — visible to management + hr ONLY.
SENSITIVE_MANAGERIAL_DATA = [
    {
        "title": "Q3 Engineering Compensation & Promotion Strategy",
        "source_type": "Confluence",
        "source_url": "https://confluence.internal/spaces/HR/q3-comp-strategy",
        "author": "Sarah Patel",
        "content": (
            "Q3 salary bands for engineering are increasing 4-6% for L3-L4, "
            "8% for L5+ in high-attrition-risk roles. Promotion packets for "
            "L4->L5 are due to the calibration committee by August 15. "
            "Budget ceiling for the payments team is $180k in net new comp."
        ),
    },
    {
        "title": "Performance Ratings — Q2 Calibration",
        "source_type": "Confluence",
        "source_url": "https://confluence.internal/spaces/HR/q2-perf-calibration",
        "author": "Sarah Patel",
        "content": (
            "Q2 calibration results by team are finalized. Distribution "
            "targets: 15% exceeds, 70% meets, 15% below. Any 'below' rating "
            "requires a documented improvement plan co-signed by HRBP before "
            "it can be delivered to the employee."
        ),
    },
]

# 3. Jira & PR context — visible to dev ONLY.
JIRA_PR_CONTEXT = [
    {
        "title": "Known Memory Leak in Auth Token Refresher",
        "source_type": "Jira",
        "source_url": "https://jira.internal/browse/AUTH-482",
        "author": "Marcus Webb",
        "content": (
            "AUTH-482: the background token-refresh goroutine leaks a "
            "context.CancelFunc on every refresh cycle when the upstream "
            "IdP times out. Workaround: restart the auth-service pod every "
            "6h via the existing CronJob until the fix in PR #931 lands."
        ),
    },
]


def _all_seed_rows() -> list[dict]:
    rows = []
    for d in PUBLIC_TECHNICAL_DOCS:
        rows.append({**d, "allowed_roles": ["dev", "management"], "allowed_groups": ["eng-payments"]})
    for d in SENSITIVE_MANAGERIAL_DATA:
        rows.append({**d, "allowed_roles": ["management", "hr"], "allowed_groups": ["management"]})
    for d in JIRA_PR_CONTEXT:
        rows.append({**d, "allowed_roles": ["dev"], "allowed_groups": ["eng-payments"]})
    return rows


async def seed() -> None:
    await init_db()
    rows = _all_seed_rows()

    embeddings = await get_embeddings_batch([r["content"] for r in rows])

    async with AsyncSessionLocal() as session:
        for row, embedding in zip(rows, embeddings):
            chunk = DocumentChunk(
                title=row["title"],
                source_type=row["source_type"],
                source_url=row["source_url"],
                content=row["content"],
                embedding=embedding,
                allowed_roles=row["allowed_roles"],
                allowed_groups=row["allowed_groups"],
                author=row["author"],
            )
            session.add(chunk)
        await session.commit()

    print(f"Seeded {len(rows)} document chunks into the vector DB.")


if __name__ == "__main__":
    asyncio.run(seed())
