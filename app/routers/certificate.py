from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin
from app.dependencies.auth import get_current_user

from app.models.user import User

from app.schemas.certificate import CertificateRegistryItem
from app.schemas.certificate import CertificateResponse

from app.services.certificate_service import get_certificate_by_id
from app.services.certificate_service import get_user_certificates
from app.services.certificate_service import list_all_certificates
from app.services.certificate_service import render_certificate_pdf
from app.services.certificate_service import render_certificate_png


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


@router.get("/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if format not in ("pdf", "png"):
        raise HTTPException(
            status_code=400,
            detail="format must be 'pdf' or 'png'"
        )

    certificate = get_certificate_by_id(db, certificate_id)

    if certificate is None:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found"
        )

    # A student may only download their own certificate; an admin may
    # download any of them.
    if current_user.role != "admin" and certificate.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorised to download this certificate"
        )

    if format == "pdf":
        content = render_certificate_pdf(certificate)
        media_type = "application/pdf"
    else:
        content = render_certificate_png(certificate)
        media_type = "image/png"

    filename = f"arnav-certificate-{certificate.certificate_number}.{format}"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


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
