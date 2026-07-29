from pydantic import BaseModel

from app.schemas.subchapter import SubchapterResponse
from app.schemas.quiz import QuizSummary


class ChapterResponse(BaseModel):
    id: int
    course_id: int
    chapter_number: int
    title: str
    description: str | None
    num_subchapters: int
    subchapters: list[SubchapterResponse] = []
    quiz: QuizSummary | None = None

    class Config:
        from_attributes = True
