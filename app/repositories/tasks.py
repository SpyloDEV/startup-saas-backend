from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, *, workspace_id: str, task_id: str) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.workspace_id == workspace_id, Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        workspace_id: str,
        limit: int,
        offset: int,
        status: TaskStatus | None = None,
        project_id: str | None = None,
        assigned_to_id: str | None = None,
    ) -> tuple[list[Task], int]:
        filters = [Task.workspace_id == workspace_id]
        if status is not None:
            filters.append(Task.status == status)
        if project_id is not None:
            filters.append(Task.project_id == project_id)
        if assigned_to_id is not None:
            filters.append(Task.assigned_to_id == assigned_to_id)

        total = await self.session.scalar(
            select(func.count()).select_from(Task).where(*filters)
        )
        result = await self.session.execute(
            select(Task)
            .where(*filters)
            .order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def create(
        self,
        *,
        workspace_id: str,
        project_id: str,
        title: str,
        description: str | None,
        status: TaskStatus,
        due_date,
        assigned_to_id: str | None,
        created_by_id: str,
    ) -> Task:
        task = Task(
            workspace_id=workspace_id,
            project_id=project_id,
            title=title,
            description=description,
            status=status,
            due_date=due_date,
            assigned_to_id=assigned_to_id,
            created_by_id=created_by_id,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()
