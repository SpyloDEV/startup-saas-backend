from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, workspace_id: str) -> Workspace | None:
        return await self.session.get(Workspace, workspace_id)

    async def get_by_slug(self, slug: str) -> Workspace | None:
        result = await self.session.execute(
            select(Workspace).where(func.lower(Workspace.slug) == slug.lower())
        )
        return result.scalar_one_or_none()

    async def create(self, *, name: str, slug: str, created_by_id: str) -> Workspace:
        workspace = Workspace(name=name, slug=slug, created_by_id=created_by_id)
        self.session.add(workspace)
        await self.session.flush()
        return workspace

    async def add_member(
        self,
        *,
        workspace_id: str,
        user_id: str,
        role: WorkspaceRole,
    ) -> WorkspaceMember:
        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def get_member(
        self,
        *,
        workspace_id: str,
        user_id: str,
        include_user: bool = False,
    ) -> WorkspaceMember | None:
        statement = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        if include_user:
            statement = statement.options(selectinload(WorkspaceMember.user))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[Workspace]:
        result = await self.session.execute(
            select(Workspace)
            .join(WorkspaceMember)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_members(self, workspace_id: str) -> list[WorkspaceMember]:
        result = await self.session.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id)
            .options(selectinload(WorkspaceMember.user))
            .order_by(WorkspaceMember.created_at.asc())
        )
        return list(result.scalars().all())
