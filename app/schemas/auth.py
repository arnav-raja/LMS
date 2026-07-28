from pydantic import BaseModel
from pydantic import EmailStr

from app.constants import Department
from app.constants import Seniority


class RegisterRequest(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    role: str
    department: Department | None = None
    seniority: Seniority | None = None

    class Config:
        from_attributes = True