import secrets

import dns.resolver

from sqlalchemy.orm import Session

from app.models.organisation import Organisation


def get_or_create_organisation(db: Session) -> Organisation:
    """This system currently supports a single organisation per
    deployment, so we fetch that one row, creating it on first use."""
    organisation = db.query(Organisation).first()

    if organisation is None:
        organisation = Organisation(name="Default Organisation")
        db.add(organisation)
        db.commit()
        db.refresh(organisation)

    return organisation


def set_custom_domain(
    db: Session,
    custom_domain: str
) -> Organisation:
    organisation = get_or_create_organisation(db)

    organisation.custom_domain = custom_domain.strip().lower()
    organisation.verification_token = secrets.token_hex(16)
    organisation.domain_verified = False

    db.commit()
    db.refresh(organisation)

    return organisation


def verify_custom_domain(db: Session) -> Organisation:
    """Looks up a TXT record at the customer's domain and checks it
    contains the verification token we issued them."""
    organisation = get_or_create_organisation(db)

    if not organisation.custom_domain or not organisation.verification_token:
        raise ValueError("No custom domain has been set yet")

    record_name = f"_arnav-verify.{organisation.custom_domain}"

    try:
        answers = dns.resolver.resolve(record_name, "TXT")
    except Exception as error:
        raise ValueError(
            f"Could not read a TXT record at {record_name}: {error}"
        )

    found = any(
        organisation.verification_token in "".join(
            part.decode() if isinstance(part, bytes) else part
            for part in answer.strings
        )
        for answer in answers
    )

    if not found:
        raise ValueError(
            "The TXT record does not contain the expected verification token"
        )

    organisation.domain_verified = True
    db.commit()
    db.refresh(organisation)

    return organisation


def remove_custom_domain(db: Session) -> Organisation:
    organisation = get_or_create_organisation(db)

    organisation.custom_domain = None
    organisation.verification_token = None
    organisation.domain_verified = False

    db.commit()
    db.refresh(organisation)

    return organisation
