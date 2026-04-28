from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: str
    workspace_id: str | None
    actor_id: str | None
    action: str
    entity_type: str
    entity_id: str | None
    context: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
