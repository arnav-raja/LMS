"""The errors the application raises on purpose.

Before this, a service had three different ways to say something went
wrong: raise `ValueError`, return `None`, or return a `(value, reason)`
tuple with a string reason. Every router then had to know which of the
three its particular service used, and translate it. That translation was
duplicated in a dozen places and was easy to get subtly wrong.

Now a service raises, the router calls it, and the handler registered in
app/main.py turns the error into the right HTTP response. A router only
still checks a status itself when the check is about *who is asking*,
which is the router's own job.

The status codes here match what the API already returned, deliberately.
A duplicate username stays 400 rather than becoming the more technically
correct 409, because the frontend already reads 400 for it and this change
is about how the code is organised, not about changing the contract.
"""


class DomainError(Exception):
    """Base for every deliberate failure. Never raised directly."""

    status_code: int = 400
    default_detail: str = "The request could not be completed"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class NotFoundError(DomainError):
    """The thing being asked for does not exist, or is not visible to the
    caller and must not be distinguishable from missing."""

    status_code = 404
    default_detail = "Not found"


class ConflictError(DomainError):
    """The request is well-formed but clashes with data already stored —
    a username someone else has, an email already registered."""

    status_code = 400
    default_detail = "That change conflicts with data that already exists"


class InvalidInputError(DomainError):
    """The request is structurally valid but breaks a rule the schema
    cannot express — a password that is too weak, for instance. Pydantic
    catches shape; this catches policy."""

    status_code = 400
    default_detail = "That value is not allowed"


class TooManyAttemptsError(DomainError):
    """The caller is being rate limited."""

    status_code = 429
    default_detail = "Too many attempts. Try again shortly."


class PermissionDeniedError(DomainError):
    """The caller is signed in but is not allowed to do this: not an admin,
    no access to the course, or trying to open a lesson still locked."""

    status_code = 403
    default_detail = "You do not have permission to do this"
