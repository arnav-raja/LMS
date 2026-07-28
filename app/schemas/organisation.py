from pydantic import BaseModel


class SetDomainRequest(BaseModel):
    custom_domain: str


class OrganisationDomainResponse(BaseModel):
    id: int
    name: str
    custom_domain: str | None = None
    verification_token: str | None = None
    domain_verified: bool

    class Config:
        from_attributes = True
