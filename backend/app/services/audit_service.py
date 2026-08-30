"""Recording what administrators do.

Only actions that change an account are recorded, because those are the
ones with no other trace. Course and quiz edits leave the content itself
as evidence; a deleted account leaves nothing at all.

`record` does not commit. It adds the entry to the same session and
transaction as the action it describes, so the two either both land or
neither does — an audit log that can disagree with what actually happened
is worse than none.
"""

from sqlalchemy.orm import Session

from app.models.audit_entry import AuditEntry
from app.models.user import User


USER_CREATED = "user.created"
USER_UPDATED = "user.updated"
USER_DELETED = "user.deleted"


def record(
    db: Session,
    actor: User,
    action: str,
    target_type: str,
    target_id: int | None,
    summary: str,
) -> AuditEntry:
    entry = AuditEntry(
        actor_id=actor.id,
        actor_name=actor.name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        summary=summary,
    )

    db.add(entry)

    return entry


def list_entries(
    db: Session,
    limit: int = 100,
) -> list[AuditEntry]:
    """Most recent first. Capped rather than paginated for now — this is
    read by a person scanning for something that looks wrong, and
    pagination arrives with the rest of it in a later phase."""
    return (
        db.query(AuditEntry)
        .order_by(AuditEntry.created_at.desc(), AuditEntry.id.desc())
        .limit(limit)
        .all()
    )


def describe_user_changes(
    changes: dict[str, object],
) -> str:
    """A readable summary of what an edit touched, without ever naming a
    value that should not be written down."""
    if not changes:
        return "no changes"

    parts = []

    for field in sorted(changes):
        if field == "password":
            parts.append("password reset")
        else:
            parts.append(f"{field} -> {changes[field]}")

    return ", ".join(parts)
