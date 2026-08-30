from pydantic import BaseModel

from app.constants import CourseStatus


class CreateSubchapterRequest(BaseModel):
    title: str
    content: str | None = None


class CreateChapterRequest(BaseModel):
    title: str
    description: str | None = None
    subchapters: list[CreateSubchapterRequest]


class CreateCourseRequest(BaseModel):
    title: str
    description: str
    status: CourseStatus = CourseStatus.DRAFT
    chapters: list[CreateChapterRequest]