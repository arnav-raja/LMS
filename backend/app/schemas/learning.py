from pydantic import BaseModel


class ContinueLearningResponse(BaseModel):
    course_id: int

    chapter_id: int
    chapter_number: int
    chapter_title: str

    subchapter_id: int
    subchapter_number: int
    subchapter_title: str


class CourseProgressResponse(BaseModel):
    course_id: int

    completed_subchapters: int
    total_subchapters: int

    completed_chapters: int
    total_chapters: int

    percentage: float