from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=2, max_length=220)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    due_date: date | None = None
    assigned_to_id: str | None = None


class TaskUpdate(BaseModel):
    project_id: str | None = None
    title: str | None = Field(default=None, min_length=2, max_length=220)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    due_date: date | None = None
    assigned_to_id: str | None = None


class TaskRead(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    title: str
    description: str | None
    status: TaskStatus
    due_date: date | None
    assigned_to_id: str | None
    created_by_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
