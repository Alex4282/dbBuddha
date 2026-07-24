from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.github_sync import load_state, sync_once

router = APIRouter(prefix="/api/v1/github", tags=["github"])


@router.post("/sync")
async def trigger_sync() -> dict:
    """Run a sync cycle right now instead of waiting for the next scheduled
    poll — the background loop (if enabled) keeps running independently."""
    try:
        return await sync_once()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def sync_status() -> dict:
    state = load_state()
    return {
        "configured": bool(settings.github_token and settings.github_owner and settings.github_repo),
        "background_polling_enabled": settings.github_sync_enabled,
        "poll_interval_seconds": settings.github_poll_interval_seconds,
        "owner": settings.github_owner,
        "repo": settings.github_repo,
        "branch": settings.github_branch,
        "last_run_at": state.get("last_run_at"),
        "tracked_files": len(state.get("files", {})),
        "tracked_issues": len(state.get("issues", {})),
        "tracked_prs": len(state.get("prs", {})),
    }
