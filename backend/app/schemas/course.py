from pydantic import BaseModel


class CourseResponse(BaseModel):
    id: int
    title: str
    description: str
    num_chapters: int
    status: str

    class Config:
        from_attributes = True
