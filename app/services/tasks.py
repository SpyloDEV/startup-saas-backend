from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.task import Task, TaskStatus
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.repositories.workspaces import WorkspaceRepository
from app.services.audit_logs import AuditLogService
from app.services.notifications import NotificationService


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.tasks = TaskRepository(session)
        self.projects = ProjectRepository(session)
        self.workspaces = WorkspaceRepository(session)
        self.audit_logs = AuditLogService(session)
        self.notifications = NotificationService(session)

    async def create_task(
        self,
        *,
        workspace_id: str,
        project_id: str,
        title: str,
        description: str | None,
        status: TaskStatus,
        due_date: date | None,
        assigned_to_id: str | None,
        actor_id: str,
    ) -> Task:
        await self._validate_project(workspace_id=workspace_id, project_id=project_id)
        if assigned_to_id is not None:
            await self._validate_assignee(
                workspace_id=workspace_id,
                assigned_to_id=assigned_to_id,
            )

        task = await self.tasks.create(
            workspace_id=workspace_id,
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            due_date=due_date,
            assigned_to_id=assigned_to_id,
            created_by_id=actor_id,
        )
        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="task_created",
            entity_type="task",
            entity_id=task.id,
            context={"title": task.title, "status": task.status.value},
        )
        if assigned_to_id is not None:
            await self.notifications.enqueue_task_assignment_email(
                workspace_id=workspace_id,
                task_id=task.id,
                assigned_to_id=assigned_to_id,
            )
        return task

    async def list_tasks(
        self,
        *,
        workspace_id: str,
        limit: int,
        offset: int,
        status: TaskStatus | None,
        project_id: str | None,
        assigned_to_id: str | None,
    ) -> tuple[list[Task], int]:
        return await self.tasks.list(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            status=status,
            project_id=project_id,
            assigned_to_id=assigned_to_id,
        )

    async def get_task(self, *, workspace_id: str, task_id: str) -> Task:
        task = await self.tasks.get(workspace_id=workspace_id, task_id=task_id)
        if task is None:
            raise NotFoundError("Task not found.")
        return task

    async def update_task(
        self,
        *,
        workspace_id: str,
        task_id: str,
        actor_id: str,
        project_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
        due_date: date | None = None,
        assigned_to_id: str | None = None,
    ) -> Task:
        task = await self.get_task(workspace_id=workspace_id, task_id=task_id)
        previous_assignee_id = task.assigned_to_id

        if project_id is not None:
            await self._validate_project(
                workspace_id=workspace_id, project_id=project_id
            )
            task.project_id = project_id
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if status is not None:
            task.status = status
        if due_date is not None:
            task.due_date = due_date
        if assigned_to_id is not None:
            await self._validate_assignee(
                workspace_id=workspace_id,
                assigned_to_id=assigned_to_id,
            )
            task.assigned_to_id = assigned_to_id

        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="task_updated",
            entity_type="task",
            entity_id=task.id,
            context={
                "title": task.title,
                "status": task.status.value,
                "assigned_to_id": task.assigned_to_id,
            },
        )
        if task.assigned_to_id and task.assigned_to_id != previous_assignee_id:
            await self.notifications.enqueue_task_assignment_email(
                workspace_id=workspace_id,
                task_id=task.id,
                assigned_to_id=task.assigned_to_id,
            )
        return task

    async def delete_task(
        self,
        *,
        workspace_id: str,
        task_id: str,
        actor_id: str,
    ) -> None:
        task = await self.get_task(workspace_id=workspace_id, task_id=task_id)
        await self.tasks.delete(task)
        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="task_deleted",
            entity_type="task",
            entity_id=task_id,
            context={"title": task.title},
        )

    async def _validate_project(self, *, workspace_id: str, project_id: str) -> None:
        project = await self.projects.get(
            workspace_id=workspace_id, project_id=project_id
        )
        if project is None:
            raise ValidationAppError("Project does not belong to this workspace.")

    async def _validate_assignee(
        self,
        *,
        workspace_id: str,
        assigned_to_id: str,
    ) -> None:
        membership = await self.workspaces.get_member(
            workspace_id=workspace_id,
            user_id=assigned_to_id,
        )
        if membership is None:
            raise ValidationAppError("Assignee must be a member of the workspace.")
