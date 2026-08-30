from pydantic import BaseModel

from app.constants import CourseStatus


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    num_chapters: int
    status: CourseStatus

    class Config:
        from_attributes = True
