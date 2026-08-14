from datetime import datetime

from sqlalchemy.orm import Session

from app.models.progress import Progress
from app.models.subchapter import Subchapter
from app.models.chapter import Chapter


def get_subchapter_course_id(
    db: Session,
    subchapter_id: int
):
    result = (
        db.query(Chapter.course_id)
        .join(Subchapter, Subchapter.chapter_id == Chapter.id)
        .filter(Subchapter.id == subchapter_id)
        .first()
    )

    return result.course_id if result else None


def complete_subchapter(
    db: Session,
    user_id: int,
    subchapter_id: int
):
    progress = (
        db.query(Progress)
        .filter(
            Progress.user_id == user_id,
            Progress.subchapter_id == subchapter_id
        )
        .first()
    )

    if progress:
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()

    else:
        progress = Progress(
            user_id=user_id,
            subchapter_id=subchapter_id,
            is_completed=True,
            completed_at=datetime.utcnow()
        )

        db.add(progress)

    db.commit()
    db.refresh(progress)

    return progress


def get_completed_subchapter_ids(
    db: Session,
    user_id: int
) -> set[int]:
    return {
        row.subchapter_id
        for row in (
            db.query(Progress.subchapter_id)
            .filter(
                Progress.user_id == user_id,
                Progress.is_completed == True
            )
            .all()
        )
    }


def get_user_progress(
    db: Session,
    user_id: int
):
    return (
        db.query(Progress)
        .filter(
            Progress.user_id == user_id
        )
        .all()
    )
