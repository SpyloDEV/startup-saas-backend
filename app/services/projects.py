from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.repositories.projects import ProjectRepository
from app.services.audit_logs import AuditLogService


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.projects = ProjectRepository(session)
        self.audit_logs = AuditLogService(session)

    async def create_project(
        self,
        *,
        workspace_id: str,
        name: str,
        description: str | None,
        actor_id: str,
    ) -> Project:
        project = await self.projects.create(
            workspace_id=workspace_id,
            name=name,
            description=description,
            created_by_id=actor_id,
        )
        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="project_created",
            entity_type="project",
            entity_id=project.id,
            context={"name": project.name},
        )
        return project

    async def list_projects(
        self,
        *,
        workspace_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Project], int]:
        return await self.projects.list(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
        )

    async def get_project(self, *, workspace_id: str, project_id: str) -> Project:
        project = await self.projects.get(
            workspace_id=workspace_id, project_id=project_id
        )
        if project is None:
            raise NotFoundError("Project not found.")
        return project

    async def update_project(
        self,
        *,
        workspace_id: str,
        project_id: str,
        actor_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> Project:
        project = await self.get_project(
            workspace_id=workspace_id, project_id=project_id
        )
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="project_updated",
            entity_type="project",
            entity_id=project.id,
            context={"name": project.name},
        )
        return project

    async def delete_project(
        self,
        *,
        workspace_id: str,
        project_id: str,
        actor_id: str,
    ) -> None:
        project = await self.get_project(
            workspace_id=workspace_id, project_id=project_id
        )
        await self.projects.delete(project)
        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="project_deleted",
            entity_type="project",
            entity_id=project_id,
            context={"name": project.name},
        )
