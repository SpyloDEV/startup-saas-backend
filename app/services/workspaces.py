import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.users import UserRepository
from app.repositories.workspaces import WorkspaceRepository
from app.services.audit_logs import AuditLogService


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workspace"


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workspaces = WorkspaceRepository(session)
        self.users = UserRepository(session)
        self.audit_logs = AuditLogService(session)

    async def create_workspace(
        self,
        *,
        name: str,
        slug: str | None,
        owner: User,
    ) -> Workspace:
        unique_slug = await self._unique_slug(slugify(slug or name))
        workspace = await self.workspaces.create(
            name=name,
            slug=unique_slug,
            created_by_id=owner.id,
        )
        await self.workspaces.add_member(
            workspace_id=workspace.id,
            user_id=owner.id,
            role=WorkspaceRole.OWNER,
        )
        await self.audit_logs.record(
            workspace_id=workspace.id,
            actor_id=owner.id,
            action="workspace_created",
            entity_type="workspace",
            entity_id=workspace.id,
            context={"name": workspace.name, "slug": workspace.slug},
        )
        return workspace

    async def list_for_user(self, user_id: str) -> list[Workspace]:
        return await self.workspaces.list_for_user(user_id)

    async def add_member(
        self,
        *,
        workspace_id: str,
        email: str,
        role: WorkspaceRole,
        actor_id: str,
    ) -> WorkspaceMember:
        if role == WorkspaceRole.OWNER:
            raise ValidationAppError("Use an ownership transfer flow to add owners.")

        user = await self.users.get_by_email(email)
        if user is None:
            raise NotFoundError("No user exists with that email address.")

        existing = await self.workspaces.get_member(
            workspace_id=workspace_id,
            user_id=user.id,
        )
        if existing is not None:
            raise ConflictError("This user is already a workspace member.")

        await self.workspaces.add_member(
            workspace_id=workspace_id,
            user_id=user.id,
            role=role,
        )
        await self.audit_logs.record(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action="workspace_member_added",
            entity_type="workspace_member",
            entity_id=user.id,
            context={"email": user.email, "role": role.value},
        )
        return await self.workspaces.get_member(
            workspace_id=workspace_id,
            user_id=user.id,
            include_user=True,
        )

    async def list_members(self, workspace_id: str) -> list[WorkspaceMember]:
        return await self.workspaces.list_members(workspace_id)

    async def _unique_slug(self, base_slug: str) -> str:
        candidate = base_slug
        suffix = 2
        while await self.workspaces.get_by_slug(candidate) is not None:
            candidate = f"{base_slug}-{suffix}"
            suffix += 1
        return candidate
