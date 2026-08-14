from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.progress import Progress
from app.models.user import User

from app.services.access_service import get_accessible_courses
from app.services.sequence_service import get_course_subchapter_sequence
from app.services.sequence_service import get_subchapter_lock_map


def list_students(
    db: Session
):
    return (
        db.query(User)
        .filter(User.role == "student")
        .order_by(User.name)
        .all()
    )


def get_student_progress_detail(
    db: Session,
    user_id: int
):
    user = db.get(User, user_id)

    if user is None:
        return None

    courses = get_accessible_courses(db, user)

    course_details = []

    for course in courses:
        sequence = get_course_subchapter_sequence(db, course.id)
        lock_map = get_subchapter_lock_map(db, user.id, course.id)

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

        chapters_by_id: dict[int, dict] = {}
        chapter_order: list[int] = []

        for chapter in sorted(course.chapters, key=lambda c: c.chapter_number):
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
        return None

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
                User.role == "student",
                or_(*conditions)
            )
            .order_by(User.name)
            .all()
        )

    sequence = get_course_subchapter_sequence(db, course_id)
    course_subchapter_ids = {subchapter.id for subchapter in sequence}
    total_subchapters = len(course_subchapter_ids)

    roster = []

    for student in students:
        progress_rows = (
            db.query(Progress)
            .filter(
                Progress.user_id == student.id,
                Progress.subchapter_id.in_(course_subchapter_ids),
                Progress.is_completed == True
            )
            .all()
        )

        completed_subchapters = len(progress_rows)

        percentage = (
            round((completed_subchapters / total_subchapters) * 100, 2)
            if total_subchapters > 0
            else 0
        )

        last_activity = None

        completed_ats = [
            row.completed_at
            for row in progress_rows
            if row.completed_at is not None
        ]

        if completed_ats:
            last_activity = max(completed_ats)

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
