from datetime import datetime

from pydantic import BaseModel
from pydantic import EmailStr

from app.constants import Department
from app.constants import Role
from app.constants import Seniority


class DashboardResponse(BaseModel):
    total_students: int
    published_courses: int
    draft_courses: int


class DepartmentOption(BaseModel):
    code: Department
    label: str


class RoleOption(BaseModel):
    value: Seniority


class UserListItem(BaseModel):
    id: int
    name: str
    username: str | None = None
    email: EmailStr | None = None
    role: Role
    department: Department | None = None
    seniority: Seniority | None = None

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    name: str
    username: str
    email: EmailStr | None = None
    password: str
    role: Role = Role.STUDENT
    department: Department | None = None
    seniority: Seniority | None = None


class UpdateUserRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: Role | None = None
    department: Department | None = None
    seniority: Seniority | None = None


class AuditEntryResponse(BaseModel):
    """One administrative action, as shown on the audit page."""
    id: int
    actor_id: int | None = None
    actor_name: str
    action: str
    target_type: str
    target_id: int | None = None
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True
