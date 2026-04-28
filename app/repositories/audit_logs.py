from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        workspace_id: str | None,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        context: dict | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            context=context or {},
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def list(
        self,
        *,
        workspace_id: str,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditLog], int]:
        filters = [AuditLog.workspace_id == workspace_id]
        total = await self.session.scalar(
            select(func.count()).select_from(AuditLog).where(*filters)
        )
        result = await self.session.execute(
            select(AuditLog)
            .where(*filters)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)
