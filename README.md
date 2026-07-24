# NexusMind

Automated, role-based engineering knowledge graph & onboarding assistant.
Ingests Confluence / Jira / Teams / GitHub context and answers onboarding
questions through a chat interface that enforces **need-to-know** access
control — the vector search itself is gated by the asker's role/group, so a
document a user can't see never reaches the LLM in the first place.

```
nexusmind/
├── backend/                 FastAPI + PostgreSQL/pgvector
│   ├── app/
│   │   ├── main.py                  <- FastAPI entrypoint
│   │   ├── core/
│   │   │   ├── config.py            <- env-driven settings
│   │   │   └── security.py          <- JWT identity + demo persona tokens
│   │   ├── db/
│   │   │   ├── database.py          <- async engine/session
│   │   │   └── models.py            <- document_chunks ORM model (ACL columns)
│   │   ├── schemas/query.py         <- request/response Pydantic models
│   │   ├── services/
│   │   │   ├── embeddings.py        <- OpenAI embedding calls
│   │   │   ├── retrieval.py         <- ★ ABAC hard-gate pre-filter query
│   │   │   └── llm.py               <- strict need-to-know system prompt
│   │   └── api/v1/
│   │       ├── query.py             <- POST /api/v1/query
│   │       └── auth.py              <- demo token issuer + GET /api/v1/sme
│   ├── scripts/seed_data.py         <- hackathon demo data w/ ACL tags
│   ├── requirements.txt
│   ├── docker-compose.yml           <- postgres/pgvector + api
│   └── .env.example
└── frontend/                 Next.js 14 (App Router) + Tailwind
    ├── app/
    │   ├── page.tsx                 <- dashboard: sidebar + chat + SME widget
    │   ├── layout.tsx
    │   └── components/
    │       ├── PersonaSwitcher.tsx  <- ★ ID-badge persona switcher
    │       ├── ChatInterface.tsx    <- ★ chat, citations, confidence, denial
    │       ├── AppDomainSidebar.tsx
    │       └── SMEWidget.tsx
    ├── lib/{api.ts,types.ts}
    └── tailwind.config.ts           <- design token system
```

## Run it locally

```bash
# 0. Local model runtime (default provider — no API key, no billing)
# Install Ollama from https://ollama.com, then pull the two models used below:
ollama pull nomic-embed-text
ollama pull llama3.2

# 1. Backend + DB
cd backend
cp .env.example .env         # defaults to the local Ollama models above;
                              # only edit OPENAI_API_KEY / ANTHROPIC_API_KEY if you
                              # switch LLM_PROVIDER / EMBEDDING_PROVIDER to a hosted one
docker compose up -d db
pip install -r requirements.txt
python -m scripts.seed_data  # populates demo docs with ACL tags
uvicorn app.main:app --reload

# 2. Frontend (separate terminal)
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local
npm run dev
```

Open http://localhost:3000.

## Demo script (matches STEP 5 of the brief)

1. With the **Alex Chen — Junior Developer** badge active, ask *"What are
   the rules for Q3 salary increases?"* → the pre-filter finds zero eligible
   chunks (dev role only), so the response is a deterministic
   **"I do not have access to that information."**, rendered with the
   redaction stamp.
2. Switch to the **Sarah Patel — Engineering Manager** badge and ask the
   same question → now `management` is in her roles, the comp-strategy
   chunk passes the pre-filter, and the answer streams back with a
   Confluence source citation and confidence score.
3. As Alex, ask *"How do I run the auth service locally?"* → this chunk is
   tagged `dev`, so it's eligible for both personas and returns the setup
   steps with a citation.

## Security model in one sentence

Every retrieval call filters `WHERE allowed_roles && user_roles OR
allowed_groups && user_groups` **before** the cosine-similarity ranking
runs — the LLM's system prompt is a second line of defense, not the
access-control mechanism itself.
