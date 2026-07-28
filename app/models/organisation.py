from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    # The customer's own domain, e.g. "learn.yourcompany.com".
    # Nullable because most organisations will simply use the
    # platform's default domain and never set one.
    custom_domain = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )

    # Random token the customer must publish as a DNS TXT record
    # to prove ownership of custom_domain before it goes live.
    verification_token = Column(
        String(64),
        nullable=True
    )

    domain_verified = Column(
        Boolean,
        nullable=False,
        default=False
    )
