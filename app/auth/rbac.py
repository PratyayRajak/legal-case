"""Role-based access control stubs.

Full implementation in Phase 8. These stubs allow routers to be wired
up and tested without real auth in Phase 1.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

security = HTTPBearer(auto_error=False)


class Role(str, Enum):
    judge = "judge"
    lawyer = "lawyer"
    admin = "admin"
    auditor = "auditor"


class CurrentUser(BaseModel):
    user_id: str
    email: str
    role: Role


def require_role(*roles: Role) -> Callable[..., Any]:
    """FastAPI dependency that enforces role membership. STUB — always passes in dev."""

    async def _check(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ) -> CurrentUser:
        # TODO Phase 8: validate JWT, check role
        return CurrentUser(user_id="stub-user", email="stub@court.gov.in", role=Role.admin)

    return _check
