from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.background_job import BackgroundJobStatus


class BackgroundJobRead(BaseModel):
    id: str
    workspace_id: str | None
    job_type: str
    status: BackgroundJobStatus
    payload: dict
    result: dict | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
