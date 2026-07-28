from pydantic import BaseModel
from pydantic import EmailStr

from app.constants import Department
from app.constants import Seniority


class DashboardResponse(BaseModel):
    students: int
    courses: int
    access_rules: int
    completed_subchapters: int


class StudentCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    department: Department | None = None
    seniority: Seniority | None = None


class StudentProfileUpdate(BaseModel):
    department: Department
    seniority: Seniority


class DepartmentOption(BaseModel):
    code: Department
    label: str


class RoleOption(BaseModel):
    value: Seniority
