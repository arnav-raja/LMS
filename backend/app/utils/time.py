from datetime import datetime
from datetime import timezone


def utc_now() -> datetime:
    """The current moment, as a timezone-aware UTC datetime.

    Replaces `datetime.utcnow()`, which is deprecated in Python 3.12 and
    was a trap before that: it returned a *naive* datetime that merely
    happened to hold UTC. Nothing recorded that it was UTC, so comparing
    one to a timezone-aware datetime raised TypeError, and any consumer
    that assumed local time read it wrongly.
    """
    return datetime.now(timezone.utc)
