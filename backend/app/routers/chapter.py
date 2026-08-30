from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.auth import get_current_user

from app.errors import NotFoundError
from app.errors import PermissionDeniedError

from app.models.user import User

from app.schemas.chapter import ChapterResponse

from app.services.access_service import user_has_access
from app.services.chapter_service import get_chapter
from app.services.chapter_service import get_chapter_for_user
from app.services.chapter_service import get_course_chapters_for_user


router = APIRouter(
    prefix="/courses/{course_id}/chapters",
    tags=["Chapters"]
)


def _require_course_access(db: Session, user: User, course_id: int) -> None:
    if not user_has_access(db, user, course_id):
        raise PermissionDeniedError("You do not have access to this course")


@router.get("", response_model=list[ChapterResponse])
def get_all(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _require_course_access(db, current_user, course_id)

    return get_course_chapters_for_user(
        db,
        course_id,
        current_user
    )


@router.get("/{chapter_id}", response_model=ChapterResponse)
def get_one(
    course_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _require_course_access(db, current_user, course_id)

    chapter = get_chapter(
        db,
        chapter_id
    )

    if chapter is None or chapter.course_id != course_id:
        # A chapter that belongs to a different course is reported as
        # missing rather than as belonging elsewhere, so the response
        # never confirms that a chapter the caller cannot reach exists.
        raise NotFoundError("Chapter not found")

    return get_chapter_for_user(
        db,
        chapter,
        current_user
    )
