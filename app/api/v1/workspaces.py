from fastapi import APIRouter, Depends, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    WorkspaceMembership,
    require_workspace_roles,
)
from app.models.workspace import WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberInvite,
    WorkspaceMemberRead,
    WorkspaceRead,
)
from app.services.workspaces import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> WorkspaceRead:
    workspace = await WorkspaceService(session).create_workspace(
        name=payload.name,
        slug=payload.slug,
        owner=current_user,
    )
    await session.commit()
    await session.refresh(workspace)
    return workspace


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(
    current_user: CurrentUser,
    session: DbSession,
) -> list[WorkspaceRead]:
    return await WorkspaceService(session).list_for_user(current_user.id)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberRead])
async def list_members(
    _member: WorkspaceMembership,
    workspace_id: str,
    session: DbSession,
) -> list[WorkspaceMemberRead]:
    return await WorkspaceService(session).list_members(workspace_id)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    payload: WorkspaceMemberInvite,
    workspace_id: str,
    current_user: CurrentUser,
    session: DbSession,
    _member=Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> WorkspaceMemberRead:
    member = await WorkspaceService(session).add_member(
        workspace_id=workspace_id,
        email=payload.email,
        role=payload.role,
        actor_id=current_user.id,
    )
    await session.commit()
    return member
