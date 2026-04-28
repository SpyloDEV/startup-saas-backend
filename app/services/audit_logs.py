from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_logs import AuditLogRepository


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AuditLogRepository(session)

    async def record(
        self,
        *,
        workspace_id: str | None,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        context: dict | None = None,
    ) -> AuditLog:
        return await self.repository.create(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            context=context,
        )

    async def list_workspace_logs(
        self,
        *,
        workspace_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        return await self.repository.list(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
        )
