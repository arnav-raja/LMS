from sqlalchemy.orm import Session

from app.constants import CourseStatus
from app.constants import Role

from app.errors import ConflictError
from app.errors import NotFoundError

from app.models.user import User
from app.models.course import Course
from app.models.certificate import Certificate
from app.models.progress import Progress
from app.models.quiz import QuizAttempt

from app.services import audit_service
from app.services.password_policy import validate_password

from app.utils.security import hash_password


def get_dashboard(
    db: Session
):
    total_students = (
        db.query(User)
        .filter(User.role == Role.STUDENT.value)
        .count()
    )

    published_courses = (
        db.query(Course)
        .filter(Course.status == CourseStatus.PUBLISHED.value)
        .count()
    )

    draft_courses = (
        db.query(Course)
        .filter(Course.status == CourseStatus.DRAFT.value)
        .count()
    )

    return {
        "total_students": total_students,
        "published_courses": published_courses,
        "draft_courses": draft_courses
    }


def list_all_users(
    db: Session
):
    return (
        db.query(User)
        .order_by(User.name)
        .all()
    )


def create_user(
    db: Session,
    actor: User,
    name: str,
    username: str,
    email: str,
    password: str,
    role: str,
    department: str | None,
    seniority: str | None
):
    validate_password(password)

    if email and db.query(User).filter(User.email == email).first():
        raise ConflictError("Email already registered")

    if db.query(User).filter(User.username == username).first():
        raise ConflictError("Username already taken")

    user = User(
        name=name,
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        department=department,
        seniority=seniority
    )

    db.add(user)
    db.flush()

    audit_service.record(
        db,
        actor=actor,
        action=audit_service.USER_CREATED,
        target_type="user",
        target_id=user.id,
        summary=f"Created {role} account '{username}'",
    )

    db.commit()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    actor: User,
    user_id: int,
    name: str | None,
    username: str | None,
    email: str | None,
    password: str | None,
    role: str | None,
    department: str | None,
    seniority: str | None,
    provided_fields: set[str]
):
    user = db.get(User, user_id)

    if user is None:
        raise NotFoundError("User not found")

    if password:
        # Checked before anything is written, so a rejected password does
        # not leave the other edits in the same request half applied.
        validate_password(password)

    original_role = user.role
    original_username = user.username

    # What actually changed, for the audit entry. Values are recorded,
    # except the password — that one is noted as having happened and
    # nothing more.
    changes: dict[str, object] = {}

    if username is not None and username != user.username:
        if db.query(User).filter(User.username == username).first():
            raise ConflictError("Username already taken")
        user.username = username
        changes["username"] = username

    if "email" in provided_fields and email != user.email:
        if email and db.query(User).filter(User.email == email).first():
            raise ConflictError("Email already registered")
        user.email = email
        changes["email"] = email

    if name is not None and name != user.name:
        user.name = name
        changes["name"] = name

    if password:
        user.password_hash = hash_password(password)
        changes["password"] = True

    if role is not None and role != user.role:
        user.role = role
        changes["role"] = role

    if "department" in provided_fields and department != user.department:
        user.department = department
        changes["department"] = department

    if "seniority" in provided_fields and seniority != user.seniority:
        user.seniority = seniority
        changes["seniority"] = seniority

    # A new password or a changed role invalidates every token already
    # issued to this account. Resetting the password of a compromised
    # account has to lock the intruder out now, not whenever their token
    # happens to expire.
    if password or (role is not None and role != original_role):
        user.token_version += 1

    if changes:
        audit_service.record(
            db,
            actor=actor,
            action=audit_service.USER_UPDATED,
            target_type="user",
            target_id=user.id,
            summary=(
                f"Edited account '{original_username}': "
                f"{audit_service.describe_user_changes(changes)}"
            ),
        )

    db.commit()
    db.refresh(user)

    return user


def delete_user(
    db: Session,
    actor: User,
    user_id: int
) -> dict[str, int]:
    """Delete an account and everything recorded against it.

    Their progress, quiz attempts and certificates go too, by database
    cascade. That is destructive and cannot be undone — a certificate is
    a record of something the person actually achieved — so the counts are
    returned and shown to the admin who asked for the deletion.

    Before the cascades existed, this could not delete anyone who had ever
    taken a quiz at all: the foreign keys refused, and the admin got a
    vague "may still have related records" message with no way forward.
    """
    user = db.get(User, user_id)

    if user is None:
        raise NotFoundError("User not found")

    removed = {
        "progress": (
            db.query(Progress)
            .filter(Progress.user_id == user_id)
            .count()
        ),
        "quiz_attempts": (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .count()
        ),
        "certificates": (
            db.query(Certificate)
            .filter(Certificate.user_id == user_id)
            .count()
        ),
    }

    audit_service.record(
        db,
        actor=actor,
        action=audit_service.USER_DELETED,
        target_type="user",
        target_id=user_id,
        summary=(
            f"Deleted account '{user.username}' "
            f"({removed['certificates']} certificates, "
            f"{removed['quiz_attempts']} quiz attempts, "
            f"{removed['progress']} lessons completed)"
        ),
    )

    db.delete(user)
    db.commit()

    return removed
