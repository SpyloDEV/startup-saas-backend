from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    WorkspaceMembership,
    require_workspace_roles,
)
from app.models.workspace import WorkspaceRole
from app.schemas.common import Message, Page
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.projects import ProjectService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/projects",
    tags=["Projects"],
)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    workspace_id: str,
    payload: ProjectCreate,
    current_user: CurrentUser,
    session: DbSession,
    _member=Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> ProjectRead:
    project = await ProjectService(session).create_project(
        workspace_id=workspace_id,
        name=payload.name,
        description=payload.description,
        actor_id=current_user.id,
    )
    await session.commit()
    await session.refresh(project)
    return project


@router.get("", response_model=Page[ProjectRead])
async def list_projects(
    _member: WorkspaceMembership,
    workspace_id: str,
    session: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[ProjectRead]:
    projects, total = await ProjectService(session).list_projects(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )
    return Page(items=projects, total=total, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    _member: WorkspaceMembership,
    workspace_id: str,
    project_id: str,
    session: DbSession,
) -> ProjectRead:
    return await ProjectService(session).get_project(
        workspace_id=workspace_id,
        project_id=project_id,
    )


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    workspace_id: str,
    project_id: str,
    payload: ProjectUpdate,
    current_user: CurrentUser,
    session: DbSession,
    _member=Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> ProjectRead:
    project = await ProjectService(session).update_project(
        workspace_id=workspace_id,
        project_id=project_id,
        actor_id=current_user.id,
        **payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    await session.refresh(project)
    return project


@router.delete("/{project_id}", response_model=Message)
async def delete_project(
    workspace_id: str,
    project_id: str,
    current_user: CurrentUser,
    session: DbSession,
    _member=Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> Message:
    await ProjectService(session).delete_project(
        workspace_id=workspace_id,
        project_id=project_id,
        actor_id=current_user.id,
    )
    await session.commit()
    return Message(message="Project deleted.")
