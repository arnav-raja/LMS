from pydantic import BaseModel

from app.constants import Department
from app.constants import Seniority


class DashboardResponse(BaseModel):
    users: int
    courses: int
    access_rules: int
    completed_subchapters: int


class UserAccessProfileUpdate(BaseModel):
    department: Department
    seniority: Seniority


class DepartmentOption(BaseModel):
    code: Department
    label: str


class RoleOption(BaseModel):
    value: Seniority
