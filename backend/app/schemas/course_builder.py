from pydantic import BaseModel

from app.constants import CourseStatus


class CreateSubchapterRequest(BaseModel):
    # The id of an existing subchapter being edited, or null for a new one.
    # This is what identifies a lesson across a save — position used to do
    # that job, which meant reordering two lessons silently handed each
    # one's completion history to the other.
    id: int | None = None
    title: str
    content: str | None = None


class CreateChapterRequest(BaseModel):
    id: int | None = None
    title: str
    description: str | None = None
    subchapters: list[CreateSubchapterRequest]


class CreateCourseRequest(BaseModel):
    title: str
    description: str
    status: CourseStatus = CourseStatus.DRAFT
    chapters: list[CreateChapterRequest]
