from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, *, workspace_id: str, project_id: str) -> Project | None:
        result = await self.session.execute(
            select(Project).where(
                Project.workspace_id == workspace_id,
                Project.id == project_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        workspace_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        filters = [Project.workspace_id == workspace_id]
        total = await self.session.scalar(
            select(func.count()).select_from(Project).where(*filters)
        )
        result = await self.session.execute(
            select(Project)
            .where(*filters)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def create(
        self,
        *,
        workspace_id: str,
        name: str,
        description: str | None,
        created_by_id: str,
    ) -> Project:
        project = Project(
            workspace_id=workspace_id,
            name=name,
            description=description,
            created_by_id=created_by_id,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()
