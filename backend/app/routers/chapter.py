from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app.dependencies.auth import get_current_user

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


@router.get("", response_model=list[ChapterResponse])
def get_all(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not user_has_access(db, current_user, course_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this course"
        )

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
    if not user_has_access(db, current_user, course_id):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this course"
        )

    chapter = get_chapter(
        db,
        chapter_id
    )

    if chapter is None:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found"
        )

    if chapter.course_id != course_id:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found in this course"
        )

    return get_chapter_for_user(
        db,
        chapter,
        current_user
    )
