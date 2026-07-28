from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.admin import require_admin

from app.schemas.organisation import OrganisationDomainResponse
from app.schemas.organisation import SetDomainRequest

from app.services.organisation_service import get_or_create_organisation
from app.services.organisation_service import remove_custom_domain
from app.services.organisation_service import set_custom_domain
from app.services.organisation_service import verify_custom_domain


router = APIRouter(
    prefix="/admin/organisation/domain",
    tags=["Custom Domain"]
)


@router.get("", response_model=OrganisationDomainResponse)
def get_domain(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    return get_or_create_organisation(db)


@router.post("", response_model=OrganisationDomainResponse)
def set_domain(
    request: SetDomainRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    return set_custom_domain(
        db=db,
        custom_domain=request.custom_domain
    )


@router.post("/verify", response_model=OrganisationDomainResponse)
def verify_domain(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    try:
        return verify_custom_domain(db)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.delete("", response_model=OrganisationDomainResponse)
def delete_domain(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    return remove_custom_domain(db)
