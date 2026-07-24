"""
Live GitHub connector.

Polls a single configured repo on an interval (see `poll_loop`) and upserts
the resulting chunks into `document_chunks`, keyed by a stable
`external_id` (e.g. "github:owner/repo:blob:README.md#0") so a re-sync
updates existing rows instead of duplicating them.

State — per-file blob SHAs and the last-seen issue/PR timestamps — is
cached in a small JSON file next to the backend so a restart doesn't force
a full re-embed of an unchanged repo, and so unchanged files/issues/PRs are
skipped on every poll after the first.

This intentionally does NOT try to infer real GitHub team/permission
mappings into roles/groups — every chunk pulled from this repo gets the
single ACL tag configured in `GITHUB_ALLOWED_ROLES` / `GITHUB_ALLOWED_GROUPS`.
Per-file/per-path ACLs would need a real mapping from GitHub team
membership, which is a decision for whoever configures the connector, not
something inferable from the API.
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.db.models import DocumentChunk
from app.services.embeddings import get_embeddings_batch

logger = logging.getLogger("nexusmind.github_sync")

STATE_PATH = Path(__file__).resolve().parents[2] / ".github_sync_state.json"

DOC_EXTENSIONS = (".md", ".mdx")
CODE_EXTENSIONS = (
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rb", ".rs",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".kt", ".swift", ".php",
)
EXCLUDED_DIR_PARTS = (
    "node_modules/", ".git/", "dist/", "build/", "__pycache__/",
    ".venv/", "venv/", ".next/", "vendor/", "target/",
)
MAX_FILE_BYTES = 200_000
CHUNK_CHARS = 1500
MAX_CHUNKS_PER_FILE = 12


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _chunk_text(text: str, max_chars: int = CHUNK_CHARS) -> list[str]:
    """Paragraph-aware fixed-size chunker — splits on blank lines first,
    hard-wraps any single paragraph that's still too long on its own."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i : i + max_chars])
                current = ""
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks[:MAX_CHUNKS_PER_FILE]


class GitHubClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {settings.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_tree(self, branch: str) -> list[dict]:
        resp = await self._client.get(
            f"/repos/{settings.github_owner}/{settings.github_repo}/git/trees/{branch}",
            params={"recursive": "1"},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("truncated"):
            logger.warning("GitHub tree response truncated — repo has more files than one API call returns")
        return [item for item in data["tree"] if item["type"] == "blob"]

    async def get_blob(self, sha: str) -> str:
        resp = await self._client.get(f"/repos/{settings.github_owner}/{settings.github_repo}/git/blobs/{sha}")
        resp.raise_for_status()
        data = resp.json()
        if data.get("encoding") != "base64":
            return ""
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")

    async def get_last_commit_author(self, path: str) -> str:
        resp = await self._client.get(
            f"/repos/{settings.github_owner}/{settings.github_repo}/commits",
            params={"path": path, "per_page": 1},
        )
        fallback = f"{settings.github_owner}/{settings.github_repo}"
        if resp.status_code != 200:
            return fallback
        commits = resp.json()
        if not commits:
            return fallback
        return commits[0].get("commit", {}).get("author", {}).get("name") or fallback

    async def get_issues(self, since: str | None) -> list[dict]:
        params = {"state": "all", "per_page": 100, "sort": "updated", "direction": "desc"}
        if since:
            params["since"] = since
        resp = await self._client.get(f"/repos/{settings.github_owner}/{settings.github_repo}/issues", params=params)
        resp.raise_for_status()
        return [item for item in resp.json() if "pull_request" not in item]

    async def get_pulls(self) -> list[dict]:
        resp = await self._client.get(
            f"/repos/{settings.github_owner}/{settings.github_repo}/pulls",
            params={"state": "all", "per_page": 100, "sort": "updated", "direction": "desc"},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_comments(self, issue_number: int, limit: int = 5) -> list[dict]:
        resp = await self._client.get(
            f"/repos/{settings.github_owner}/{settings.github_repo}/issues/{issue_number}/comments",
            params={"per_page": limit},
        )
        if resp.status_code != 200:
            return []
        return resp.json()[:limit]


async def _upsert_chunks(session: AsyncSession, rows: list[dict]) -> int:
    if not rows:
        return 0
    embeddings = await get_embeddings_batch([r["content"] for r in rows])
    for row, embedding in zip(rows, embeddings):
        stmt = (
            pg_insert(DocumentChunk)
            .values(
                title=row["title"],
                source_type="GitHub",
                source_url=row["source_url"],
                content=row["content"],
                embedding=embedding,
                allowed_roles=row["allowed_roles"],
                allowed_groups=row["allowed_groups"],
                author=row["author"],
                external_id=row["external_id"],
            )
            .on_conflict_do_update(
                index_elements=[DocumentChunk.external_id],
                set_={
                    "title": row["title"],
                    "content": row["content"],
                    "embedding": embedding,
                    "source_url": row["source_url"],
                    "author": row["author"],
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        )
        await session.execute(stmt)
    await session.commit()
    return len(rows)


async def _delete_stale(session: AsyncSession, external_ids: list[str]) -> int:
    if not external_ids:
        return 0
    result = await session.execute(delete(DocumentChunk).where(DocumentChunk.external_id.in_(external_ids)))
    await session.commit()
    return result.rowcount or 0


async def sync_once() -> dict:
    """Run one full poll cycle: diff the repo tree + issues/PRs against the
    last-seen state, upsert anything new/changed, delete anything removed
    from the repo since the last poll. Returns a summary dict."""
    if not (settings.github_token and settings.github_owner and settings.github_repo):
        raise RuntimeError("GITHUB_TOKEN / GITHUB_OWNER / GITHUB_REPO must be set to sync")

    roles = [r.strip() for r in settings.github_allowed_roles.split(",") if r.strip()]
    groups = [g.strip() for g in settings.github_allowed_groups.split(",") if g.strip()]
    owner, repo, branch = settings.github_owner, settings.github_repo, settings.github_branch

    state = load_state()

    prior_owner, prior_repo = state.get("owner"), state.get("repo")
    if prior_owner and prior_repo and (prior_owner, prior_repo) != (owner, repo):
        # The connector was pointed at a different repo last run — every
        # cached path/issue/PR number in `state` describes files that don't
        # exist in the new repo, so keeping it would just orphan the old
        # repo's chunks (they'd fall out of tracking without ever being
        # deleted). Wipe both the old repo's rows and the cached state.
        logger.info("GitHub connector repo changed (%s/%s -> %s/%s) — clearing old chunks and sync state", prior_owner, prior_repo, owner, repo)
        async with AsyncSessionLocal() as cleanup_session:
            await cleanup_session.execute(
                delete(DocumentChunk).where(DocumentChunk.external_id.like(f"github:{prior_owner}/{prior_repo}:%"))
            )
            await cleanup_session.commit()
        state = {}

    known_files: dict = state.get("files", {})  # path -> {sha, external_ids}
    known_issues: dict = state.get("issues", {})  # number -> external_id
    known_prs: dict = state.get("prs", {})  # number -> external_id
    prs_synced_at: dict = state.get("prs_synced_at", {})
    last_issue_sync: str | None = state.get("last_issue_sync")

    client = GitHubClient()
    rows: list[dict] = []
    seen_files: set[str] = set()
    seen_issues: set[str] = set()
    seen_prs: set[str] = set()

    try:
        tree = await client.get_tree(branch)

        def eligible(f: dict, exts: tuple[str, ...]) -> bool:
            return (
                f["path"].endswith(exts)
                and not any(x in f["path"] for x in EXCLUDED_DIR_PARTS)
                and f.get("size", 0) <= MAX_FILE_BYTES
            )

        doc_files = [f for f in tree if eligible(f, DOC_EXTENSIONS)][: settings.github_max_doc_files]
        code_files = [f for f in tree if eligible(f, CODE_EXTENSIONS)][: settings.github_max_code_files]

        for f in doc_files + code_files:
            path, sha = f["path"], f["sha"]
            seen_files.add(path)
            cached = known_files.get(path)
            if cached and cached.get("sha") == sha:
                continue  # unchanged since last poll — skip re-fetch/re-embed

            content = await client.get_blob(sha)
            if not content.strip():
                continue
            author = await client.get_last_commit_author(path)
            chunks = _chunk_text(content)
            file_external_ids = []
            for i, chunk in enumerate(chunks):
                ext_id = f"github:{owner}/{repo}:blob:{path}#{i}"
                file_external_ids.append(ext_id)
                rows.append(
                    {
                        "external_id": ext_id,
                        "title": f"{path} (part {i + 1}/{len(chunks)})" if len(chunks) > 1 else path,
                        "source_url": f"https://github.com/{owner}/{repo}/blob/{branch}/{path}",
                        "content": chunk,
                        "author": author,
                        "allowed_roles": roles,
                        "allowed_groups": groups,
                    }
                )
            known_files[path] = {"sha": sha, "external_ids": file_external_ids}

        issues = await client.get_issues(since=last_issue_sync)
        for issue in issues[: settings.github_max_issues]:
            number = str(issue["number"])
            seen_issues.add(number)
            comments = await client.get_comments(issue["number"]) if issue.get("comments", 0) else []
            body_parts = [issue.get("body") or ""]
            body_parts += [f"[comment by {c['user']['login']}]: {c.get('body') or ''}" for c in comments]
            content = "\n\n".join(p for p in body_parts if p.strip())[:4000] or issue["title"]
            ext_id = f"github:{owner}/{repo}:issue:{number}"
            rows.append(
                {
                    "external_id": ext_id,
                    "title": f"Issue #{number}: {issue['title']}",
                    "source_url": issue["html_url"],
                    "content": content,
                    "author": issue["user"]["login"],
                    "allowed_roles": roles,
                    "allowed_groups": groups,
                }
            )
            known_issues[number] = ext_id

        # PRs have no `since` filter — walk newest-first and skip anything
        # whose updated_at we've already synced.
        prs = await client.get_pulls()
        for pr in prs[: settings.github_max_prs]:
            number = str(pr["number"])
            seen_prs.add(number)
            if number in known_prs and pr["updated_at"] <= prs_synced_at.get(number, ""):
                continue
            comments = await client.get_comments(pr["number"]) if pr.get("comments", 0) else []
            body_parts = [pr.get("body") or ""]
            body_parts += [f"[comment by {c['user']['login']}]: {c.get('body') or ''}" for c in comments]
            content = "\n\n".join(p for p in body_parts if p.strip())[:4000] or pr["title"]
            ext_id = f"github:{owner}/{repo}:pr:{number}"
            rows.append(
                {
                    "external_id": ext_id,
                    "title": f"PR #{number}: {pr['title']}",
                    "source_url": pr["html_url"],
                    "content": content,
                    "author": pr["user"]["login"],
                    "allowed_roles": roles,
                    "allowed_groups": groups,
                }
            )
            known_prs[number] = ext_id
            prs_synced_at[number] = pr["updated_at"]
    finally:
        await client.aclose()

    # Anything tracked from a previous poll but absent this time was removed
    # from the repo (or fell outside the caps above).
    removed_external_ids: list[str] = []
    for path in list(known_files):
        if path not in seen_files:
            removed_external_ids.extend(known_files[path].get("external_ids", []))
            del known_files[path]
    for number in list(known_issues):
        if number not in seen_issues:
            removed_external_ids.append(known_issues[number])
            del known_issues[number]
    for number in list(known_prs):
        if number not in seen_prs:
            removed_external_ids.append(known_prs[number])
            del known_prs[number]
            prs_synced_at.pop(number, None)

    async with AsyncSessionLocal() as session:
        upserted = await _upsert_chunks(session, rows)
        deleted = await _delete_stale(session, removed_external_ids)

    state.update(
        {
            "owner": owner,
            "repo": repo,
            "files": known_files,
            "issues": known_issues,
            "prs": known_prs,
            "prs_synced_at": prs_synced_at,
            "last_issue_sync": datetime.now(timezone.utc).isoformat(),
            "last_run_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    save_state(state)

    summary = {
        "upserted": upserted,
        "deleted": deleted,
        "files_seen": len(seen_files),
        "issues_seen": len(seen_issues),
        "prs_seen": len(seen_prs),
    }
    logger.info("GitHub sync complete: %s", summary)
    return summary


async def poll_loop() -> None:
    """Runs for the lifetime of the app when GITHUB_SYNC_ENABLED=true."""
    while True:
        try:
            await sync_once()
        except Exception:
            logger.exception("GitHub sync cycle failed — will retry next interval")
        await asyncio.sleep(settings.github_poll_interval_seconds)
