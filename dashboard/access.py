"""Role-based authorization rules for Phase 7 dashboard views."""

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """Supported MediciMess dashboard roles."""

    MANAGING_DIRECTOR = "managing_director"
    BRANCH_MANAGER = "branch_manager"


@dataclass(frozen=True)
class UserAccess:
    """Authenticated user's role and optional assigned branch."""

    username: str
    role: Role
    branch: str | None = None


def can_view_network(user: UserAccess) -> bool:
    """Return whether the user may access consolidated network data."""
    return user.role == Role.MANAGING_DIRECTOR


def can_view_branch(user: UserAccess, branch: str) -> bool:
    """Return whether the user may access the requested branch."""
    return user.role == Role.MANAGING_DIRECTOR or user.branch == branch
