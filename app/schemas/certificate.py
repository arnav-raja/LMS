from datetime import datetime

from pydantic import BaseModel


class CertificateResponse(BaseModel):
    """A student's own certificate."""
    id: int
    course_id: int
    course_title: str
    certificate_number: str
    issued_at: datetime


class CertificateRegistryItem(BaseModel):
    """One row in the admin-wide certificate registry."""
    id: int
    user_id: int
    user_name: str
    user_email: str | None = None
    course_id: int
    course_title: str
    certificate_number: str
    issued_at: datetime
