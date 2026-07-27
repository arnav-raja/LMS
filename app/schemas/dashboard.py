from pydantic import BaseModel


class DashboardCourse(BaseModel):
    id: int
    title: str
    progress: float
    next_subchapter: str | None


class DashboardResponse(BaseModel):
    id: int
    name: str
    email: str
    courses: list[DashboardCourse]