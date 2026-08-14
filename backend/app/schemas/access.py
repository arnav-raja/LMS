from pydantic import BaseModel

from app.constants import Department
from app.constants import Seniority


class GrantAccessRequest(BaseModel):
    department: Department
    seniority: Seniority


class CourseAccessRuleResponse(BaseModel):
    id: int
    course_id: int
    department: Department
    seniority: Seniority

    class Config:
        from_attributes = True
