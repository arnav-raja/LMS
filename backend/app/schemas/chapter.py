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


class AdminChapterListItem(BaseModel):
    """One row in the chapter picker on the admin Quizzes page."""
    id: int
    chapter_number: int
    title: str
    course_id: int
    course_title: str
    has_quiz: bool
