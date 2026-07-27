from datetime import datetime

from pydantic import BaseModel

from app.constants import Department
from app.constants import Seniority


class StudentSummary(BaseModel):
    id: int
    name: str
    email: str
    department: Department | None
    seniority: Seniority | None

    class Config:
        from_attributes = True


class SubchapterProgressDetail(BaseModel):
    id: int
    subchapter_number: int
    title: str
    is_completed: bool
    is_locked: bool
    completed_at: datetime | None


class ChapterProgressDetail(BaseModel):
    id: int
    chapter_number: int
    title: str
    subchapters: list[SubchapterProgressDetail]


class CourseProgressDetail(BaseModel):
    course_id: int
    title: str
    percentage: float
    chapters: list[ChapterProgressDetail]


class StudentProgressResponse(BaseModel):
    id: int
    name: str
    email: str
    department: Department | None
    seniority: Seniority | None
    courses: list[CourseProgressDetail]


class CourseRosterEntry(BaseModel):
    id: int
    name: str
    email: str
    department: Department | None
    seniority: Seniority | None
    completed_subchapters: int
    total_subchapters: int
    percentage: float
    last_activity: datetime | None


class CourseRosterResponse(BaseModel):
    course_id: int
    course_title: str
    students: list[CourseRosterEntry]
