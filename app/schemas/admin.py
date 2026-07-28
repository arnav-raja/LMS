from pydantic import BaseModel
from pydantic import EmailStr

from app.constants import Department
from app.constants import Seniority


class DashboardResponse(BaseModel):
    total_students: int
    published_courses: int
    draft_courses: int
    students_without_access: int
    average_completion_percentage: float
    completions_last_7_days: int


class UserAccessProfileUpdate(BaseModel):
    department: Department
    seniority: Seniority


class DepartmentOption(BaseModel):
    code: Department
    label: str


class RoleOption(BaseModel):
    value: Seniority


class UserListItem(BaseModel):
    id: int
    name: str
    username: str | None = None
    email: EmailStr
    role: str
    department: Department | None = None
    seniority: Seniority | None = None

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str
    role: str = "student"
    department: Department | None = None
    seniority: Seniority | None = None


class UpdateUserRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: str | None = None
    department: Department | None = None
    seniority: Seniority | None = None
