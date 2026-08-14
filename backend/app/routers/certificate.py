from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.certificate import CertificateRegistryItem
from app.schemas.certificate import CertificateResponse

from app.services.certificate_service import get_user_certificates
from app.services.certificate_service import list_all_certificates


router = APIRouter(tags=["Certificates"])


@router.get("/certificates/me", response_model=list[CertificateResponse])
def my_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certificates = get_user_certificates(db, current_user.id)

    return [
        {
            "id": certificate.id,
            "course_id": certificate.course_id,
            "course_title": certificate.course.title,
            "certificate_number": certificate.certificate_number,
            "issued_at": certificate.issued_at
        }
        for certificate in certificates
    ]


@router.get(
    "/admin/certificates",
    response_model=list[CertificateRegistryItem]
)
def all_certificates(
    course_id: int | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    certificates = list_all_certificates(db, course_id)

    return [
        {
            "id": certificate.id,
            "user_id": certificate.user_id,
            "user_name": certificate.user.name,
            "user_email": certificate.user.email,
            "course_id": certificate.course_id,
            "course_title": certificate.course.title,
            "certificate_number": certificate.certificate_number,
            "issued_at": certificate.issued_at
        }
        for certificate in certificates
    ]
