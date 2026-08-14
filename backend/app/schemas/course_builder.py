from pydantic import BaseModel


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
    status: str = "draft"
    chapters: list[CreateChapterRequest]