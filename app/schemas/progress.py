from pydantic import BaseModel


class CompleteSubchapterRequest(BaseModel):
    subchapter_id: int


class ProgressResponse(BaseModel):
    id: int
    user_id: int
    subchapter_id: int
    is_completed: bool

    class Config:
        from_attributes = True