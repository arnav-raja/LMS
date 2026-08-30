from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.constants import Role

from app.errors import NotFoundError

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.progress import Progress
from app.models.user import User

from app.services.access_service import get_accessible_courses
from app.services.sequence_service import get_course_subchapter_sequence
from app.services.sequence_service import get_course_subchapter_sequences
from app.services.sequence_service import get_subchapter_lock_maps


def list_students(
    db: Session
):
    return (
        db.query(User)
        .filter(User.role == Role.STUDENT.value)
        .order_by(User.name)
        .all()
    )


def get_student_progress_detail(
    db: Session,
    user_id: int
):
    user = db.get(User, user_id)

    if user is None:
        raise NotFoundError("Student not found")

    courses = get_accessible_courses(db, user)
    course_ids = [course.id for course in courses]

    # All three of these used to be resolved inside the loop below, so the
    # cost of this page grew with the size of the catalogue rather than
    # with the student being looked at. The lock map alone was five or six
    # queries per course.
    sequences = get_course_subchapter_sequences(db, course_ids)
    lock_maps = get_subchapter_lock_maps(db, user.id, course_ids)

    # `course.chapters` is a lazy relationship, so reading it inside the
    # loop was another query per course. One query for all of them here.
    chapters_by_course: dict[int, list[Chapter]] = {
        course_id: [] for course_id in course_ids
    }

    if course_ids:
        for chapter in (
            db.query(Chapter)
            .filter(Chapter.course_id.in_(course_ids))
            .order_by(Chapter.course_id, Chapter.chapter_number)
            .all()
        ):
            chapters_by_course[chapter.course_id].append(chapter)

    completed_at_by_subchapter = {
        row.subchapter_id: row.completed_at
        for row in (
            db.query(Progress.subchapter_id, Progress.completed_at)
            .filter(
                Progress.user_id == user.id,
                Progress.is_completed == True
            )
            .all()
        )
    }

    course_details = []

    for course in courses:
        sequence = sequences.get(course.id, [])
        lock_map = lock_maps.get(course.id, {})

        chapters_by_id: dict[int, dict] = {}
        chapter_order: list[int] = []

        for chapter in chapters_by_course.get(course.id, []):
            chapters_by_id[chapter.id] = {
                "id": chapter.id,
                "chapter_number": chapter.chapter_number,
                "title": chapter.title,
                "subchapters": []
            }
            chapter_order.append(chapter.id)

        total = len(sequence)
        completed = 0

        for subchapter in sequence:
            entry = lock_map.get(
                subchapter.id,
                {"is_completed": False, "is_locked": True}
            )

            if entry["is_completed"]:
                completed += 1

            chapters_by_id[subchapter.chapter_id]["subchapters"].append(
                {
                    "id": subchapter.id,
                    "subchapter_number": subchapter.subchapter_number,
                    "title": subchapter.title,
                    "is_completed": entry["is_completed"],
                    "is_locked": entry["is_locked"],
                    "completed_at": completed_at_by_subchapter.get(subchapter.id)
                }
            )

        percentage = round((completed / total) * 100, 2) if total > 0 else 0

        course_details.append(
            {
                "course_id": course.id,
                "title": course.title,
                "percentage": percentage,
                "chapters": [chapters_by_id[cid] for cid in chapter_order]
            }
        )

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "department": user.department,
        "seniority": user.seniority,
        "courses": course_details
    }


def get_course_roster(
    db: Session,
    course_id: int
):
    course = db.get(Course, course_id)

    if course is None:
        raise NotFoundError("Course not found")

    rules = (
        db.query(CourseAccessRule)
        .filter(CourseAccessRule.course_id == course_id)
        .all()
    )

    department_seniority_pairs = {
        (rule.department, rule.seniority) for rule in rules
    }

    students = []

    if department_seniority_pairs:
        conditions = [
            and_(
                User.department == department,
                User.seniority == seniority
            )
            for department, seniority in department_seniority_pairs
        ]

        students = (
            db.query(User)
            .filter(
                User.role == Role.STUDENT.value,
                or_(*conditions)
            )
            .order_by(User.name)
            .all()
        )

    sequence = get_course_subchapter_sequence(db, course_id)
    course_subchapter_ids = {subchapter.id for subchapter in sequence}
    total_subchapters = len(course_subchapter_ids)

    # One grouped query for the whole roster. This used to run a query per
    # student and count the rows in Python, so opening the roster of a
    # course a whole department can reach cost one round trip per person
    # on it.
    progress_by_student: dict[int, tuple[int, object]] = {}

    if students and course_subchapter_ids:
        for row in (
            db.query(
                Progress.user_id,
                func.count(Progress.id).label("completed"),
                func.max(Progress.completed_at).label("last_activity"),
            )
            .filter(
                Progress.user_id.in_([student.id for student in students]),
                Progress.subchapter_id.in_(course_subchapter_ids),
                Progress.is_completed == True
            )
            .group_by(Progress.user_id)
            .all()
        ):
            progress_by_student[row.user_id] = (
                row.completed,
                row.last_activity,
            )

    roster = []

    for student in students:
        completed_subchapters, last_activity = progress_by_student.get(
            student.id, (0, None)
        )

        percentage = (
            round((completed_subchapters / total_subchapters) * 100, 2)
            if total_subchapters > 0
            else 0
        )

        roster.append(
            {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "department": student.department,
                "seniority": student.seniority,
                "completed_subchapters": completed_subchapters,
                "total_subchapters": total_subchapters,
                "percentage": percentage,
                "last_activity": last_activity
            }
        )

    return {
        "course_id": course.id,
        "course_title": course.title,
        "students": roster
    }
