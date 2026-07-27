from pydantic import BaseModel


class SubchapterResponse(BaseModel):
    id: int
    chapter_id: int
    subchapter_number: int
    title: str
    content: str | None
    is_completed: bool
    is_locked: bool

    class Config:
        from_attributes = True
