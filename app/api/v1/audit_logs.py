from fastapi import APIRouter, Depends, Query

from app.api.deps import DbSession, require_workspace_roles
from app.models.workspace import WorkspaceRole
from app.schemas.audit_log import AuditLogRead
from app.schemas.common import Page
from app.services.audit_logs import AuditLogService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/audit-logs",
    tags=["Audit Logs"],
)


@router.get("", response_model=Page[AuditLogRead])
async def list_audit_logs(
    workspace_id: str,
    session: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _member=Depends(require_workspace_roles(WorkspaceRole.OWNER, WorkspaceRole.ADMIN)),
) -> Page[AuditLogRead]:
    logs, total = await AuditLogService(session).list_workspace_logs(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )
    return Page(items=logs, total=total, limit=limit, offset=offset)
