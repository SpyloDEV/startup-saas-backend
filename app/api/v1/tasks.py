from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    CurrentUser,
    DbSession,
    WorkspaceMembership,
    require_workspace_roles,
)
from app.models.task import TaskStatus
from app.models.workspace import WorkspaceRole
from app.schemas.common import Message, Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.tasks import TaskService

router = APIRouter(prefix="/workspaces/{workspace_id}/tasks", tags=["Tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    _member: WorkspaceMembership,
    workspace_id: str,
    payload: TaskCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> TaskRead:
    task = await TaskService(session).create_task(
        workspace_id=workspace_id,
        actor_id=current_user.id,
        **payload.model_dump(),
    )
    await session.commit()
    await session.refresh(task)
    return task


@router.get("", response_model=Page[TaskRead])
async def list_tasks(
    _member: WorkspaceMembership,
    workspace_id: str,
    session: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    project_id: str | None = Query(default=None),
    assigned_to_id: str | None = Query(default=None),
) -> Page[TaskRead]:
    tasks, total = await TaskService(session).list_tasks(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
        status=status_filter,
        project_id=project_id,
        assigned_to_id=assigned_to_id,
    )
    return Page(items=tasks, total=total, limit=limit, offset=offset)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    _member: WorkspaceMembership,
    workspace_id: str,
    task_id: str,
    session: DbSession,
) -> TaskRead:
    return await TaskService(session).get_task(
        workspace_id=workspace_id,
        task_id=task_id,
    )


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    _member: WorkspaceMembership,
    workspace_id: str,
    task_id: str,
    payload: TaskUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> TaskRead:
    task = await TaskService(session).update_task(
        workspace_id=workspace_id,
        task_id=task_id,
        actor_id=current_user.id,
        **payload.model_dump(exclude_unset=True),
    )
    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/{task_id}", response_model=Message)
async def delete_task(
    workspace_id: str,
    task_id: str,
    current_user: CurrentUser,
    session: DbSession,
    _member=Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> Message:
    await TaskService(session).delete_task(
        workspace_id=workspace_id,
        task_id=task_id,
        actor_id=current_user.id,
    )
    await session.commit()
    return Message(message="Task deleted.")
