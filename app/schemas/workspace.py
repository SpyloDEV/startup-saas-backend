from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.workspace import WorkspaceRole
from app.schemas.user import UserRead


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str | None = Field(default=None, min_length=2, max_length=180)


class WorkspaceRead(BaseModel):
    id: str
    name: str
    slug: str
    created_by_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberRead(BaseModel):
    workspace_id: str
    user_id: str
    role: WorkspaceRole
    created_at: datetime
    user: UserRead

    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberInvite(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.MEMBER
