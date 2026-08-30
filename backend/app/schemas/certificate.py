from datetime import datetime

from pydantic import BaseModel


class CertificateResponse(BaseModel):
    """A student's own certificate."""
    id: int
    course_id: int
    course_title: str
    certificate_number: str
    issued_at: datetime


class CertificateVerification(BaseModel):
    """What a certificate's number proves, to anyone holding it.

    Served without authentication, so it carries the least that still
    makes it useful: enough to confirm the person named on the certificate
    completed the course named on it, and nothing else. No email, no
    account id, no scores, no department — none of which a recruiter
    checking a certificate has any business seeing.
    """
    certificate_number: str
    holder_name: str
    course_title: str
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
