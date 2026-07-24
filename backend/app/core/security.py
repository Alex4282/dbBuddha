"""
Identity & access layer.

In production this JWT would be minted by Auth0 / NextAuth (SSO -> Entra ID /
Google Workspace) and FastAPI would only ever *verify* it against the
issuer's JWKS. For hackathon speed we mint and verify the same HS256 token
ourselves, but the shape of the claims (`roles`, `groups`) is exactly what a
real SSO provider would pass through as custom claims — swapping in a real
issuer later is a config change, not a rewrite.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/mock-token", auto_error=False)


class UserContext(BaseModel):
    user_id: str
    display_name: str
    roles: list[str]
    groups: list[str]


# Demo personas for the hackathon "Persona Switcher" — STEP 4 of the brief.
# Swap this dict for a real user directory lookup in production.
DEMO_PERSONAS: dict[str, UserContext] = {
    "junior_dev": UserContext(
        user_id="alex.chen",
        display_name="Alex Chen — Junior Developer",
        roles=["dev"],
        groups=["eng-payments"],
    ),
    "eng_manager": UserContext(
        user_id="sarah.patel",
        display_name="Sarah Patel — Engineering Manager",
        roles=["management", "dev"],
        groups=["eng-payments", "management"],
    ),
}


def create_access_token(user: UserContext) -> str:
    payload = {
        "sub": user.user_id,
        "name": user.display_name,
        "roles": user.roles,
        "groups": user.groups,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> UserContext:
    """Decode the bearer JWT and extract (user_id, roles, groups).

    This is the ONLY place identity enters the system. Every downstream
    query — including the vector pre-filter — is derived from these claims,
    never from a client-supplied role/group parameter.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_error
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    return UserContext(
        user_id=user_id,
        display_name=payload.get("name", user_id),
        roles=payload.get("roles", []),
        groups=payload.get("groups", []),
    )
