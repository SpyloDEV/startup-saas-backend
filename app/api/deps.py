from collections.abc import AsyncGenerator, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedError
from app.core.security import decode_access_token
from app.db.session import get_db as session_get_db
from app.models.user import User
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.repositories.users import UserRepository
from app.repositories.workspaces import WorkspaceRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in session_get_db():
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
Token = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(token: Token, session: DbSession) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_workspace_member(
    workspace_id: str,
    current_user: CurrentUser,
    session: DbSession,
) -> WorkspaceMember:
    member = await WorkspaceRepository(session).get_member(
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
    if member is None:
        raise PermissionDeniedError("You do not have access to this workspace.")
    return member


WorkspaceMembership = Annotated[WorkspaceMember, Depends(get_workspace_member)]


def require_workspace_roles(
    *allowed_roles: WorkspaceRole,
) -> Callable[[WorkspaceMembership], WorkspaceMember]:
    async def dependency(member: WorkspaceMembership) -> WorkspaceMember:
        if member.role not in allowed_roles:
            allowed = ", ".join(role.value for role in allowed_roles)
            raise PermissionDeniedError(
                f"This action requires one of these roles: {allowed}."
            )
        return member

    return dependency
