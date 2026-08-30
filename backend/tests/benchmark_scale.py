"""A rough load check, run by hand rather than by pytest.

    docker compose --profile test up -d test-db
    python -m tests.benchmark_scale

Seeds a company-sized dataset — more people and more content than this
deployment is likely to see — and times the pages that read the most.
The point is to decide what actually needs an index or pagination with
numbers rather than by guessing, and to have a baseline to compare
against the next time something here is rewritten.

It builds its own throwaway database and drops it afterwards.
"""

import os
import time

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://lms_test:lms_test@localhost:55432/lms_test",
)
BENCH_DATABASE = "lms_benchmark"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL.rsplit("/", 1)[0] + f"/{BENCH_DATABASE}"
os.environ.setdefault("SECRET_KEY", "benchmark-secret")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.constants import Department, Role, Seniority  # noqa: E402
from app.database import Base  # noqa: E402
import app.models  # noqa: F401,E402
from app.models.chapter import Chapter  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.course_access_rule import CourseAccessRule  # noqa: E402
from app.models.progress import Progress  # noqa: E402
from app.models.subchapter import Subchapter  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import dashboard_service, tracking_service  # noqa: E402
from app.services.access_service import get_accessible_courses  # noqa: E402
from app.services.chapter_service import get_course_chapters_for_user  # noqa: E402
from app.utils.time import utc_now  # noqa: E402


STUDENTS = 800
COURSES = 40
CHAPTERS_PER_COURSE = 8
LESSONS_PER_CHAPTER = 5


def build_database():
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{BENCH_DATABASE}"'))
        connection.execute(text(f'CREATE DATABASE "{BENCH_DATABASE}"'))

    admin_engine.dispose()

    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(bind=engine)
    return engine


def drop_database():
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{BENCH_DATABASE}"'))
    admin_engine.dispose()


def seed(db):
    departments = [d.value for d in Department]
    seniorities = [s.value for s in Seniority]

    students = []
    for index in range(STUDENTS):
        students.append(
            User(
                name=f"Student {index}",
                username=f"student{index}",
                email=f"student{index}@example.com",
                password_hash="x",
                role=Role.STUDENT.value,
                department=departments[index % len(departments)],
                seniority=seniorities[index % len(seniorities)],
            )
        )
    db.add_all(students)
    db.flush()

    subchapter_ids_by_course = {}

    for course_index in range(COURSES):
        course = Course(
            title=f"Course {course_index}",
            description="Description",
            status="published",
            num_chapters=CHAPTERS_PER_COURSE,
        )
        db.add(course)
        db.flush()

        # Every course reachable by three department/seniority pairs.
        for offset in range(3):
            db.add(
                CourseAccessRule(
                    course_id=course.id,
                    department=departments[(course_index + offset) % len(departments)],
                    seniority=seniorities[(course_index + offset) % len(seniorities)],
                )
            )

        subchapter_ids_by_course[course.id] = []

        for chapter_number in range(1, CHAPTERS_PER_COURSE + 1):
            chapter = Chapter(
                course_id=course.id,
                chapter_number=chapter_number,
                title=f"Chapter {chapter_number}",
                num_subchapters=LESSONS_PER_CHAPTER,
            )
            db.add(chapter)
            db.flush()

            for lesson_number in range(1, LESSONS_PER_CHAPTER + 1):
                subchapter = Subchapter(
                    chapter_id=chapter.id,
                    subchapter_number=lesson_number,
                    title=f"Lesson {lesson_number}",
                    content="Body text",
                )
                db.add(subchapter)
                db.flush()
                subchapter_ids_by_course[course.id].append(subchapter.id)

    db.flush()

    # Every student partway through everything they can reach.
    progress = []
    for student in students:
        reachable = get_accessible_courses(db, student)
        for course in reachable:
            ids = subchapter_ids_by_course[course.id]
            for subchapter_id in ids[: len(ids) // 2]:
                progress.append(
                    Progress(
                        user_id=student.id,
                        subchapter_id=subchapter_id,
                        is_completed=True,
                        completed_at=utc_now(),
                    )
                )

    db.add_all(progress)
    db.commit()

    return students, len(progress)


def time_it(label, call, runs=5):
    call()  # warm up
    started = time.perf_counter()
    for _ in range(runs):
        result = call()
    elapsed = (time.perf_counter() - started) / runs * 1000
    print(f"  {label:<38} {elapsed:7.1f} ms")
    return result


def main():
    engine = build_database()
    session = sessionmaker(bind=engine)()

    try:
        print(
            f"Seeding {STUDENTS} students, {COURSES} courses, "
            f"{COURSES * CHAPTERS_PER_COURSE * LESSONS_PER_CHAPTER} lessons..."
        )
        started = time.perf_counter()
        students, progress_rows = seed(session)
        print(
            f"  done in {time.perf_counter() - started:.1f}s "
            f"({progress_rows} progress rows)\n"
        )

        student = students[0]
        course_id = session.query(Course.id).first().id

        print("Timings (average of 5 runs):")
        time_it(
            "student dashboard",
            lambda: dashboard_service.get_dashboard(session, student),
        )
        time_it(
            "course player (one course)",
            lambda: get_course_chapters_for_user(session, course_id, student),
        )
        time_it(
            "admin: course roster",
            lambda: tracking_service.get_course_roster(session, course_id),
        )
        time_it(
            "admin: student progress detail",
            lambda: tracking_service.get_student_progress_detail(
                session, student.id
            ),
        )
        time_it(
            "admin: list students",
            lambda: tracking_service.list_students(session),
        )

        print("\nEXPLAIN — courses a student can reach:")
        plan = session.execute(
            text(
                """
                EXPLAIN ANALYZE
                SELECT DISTINCT courses.* FROM courses
                JOIN course_access_rules
                  ON course_access_rules.course_id = courses.id
                WHERE courses.status = 'published'
                  AND course_access_rules.department = :department
                  AND course_access_rules.seniority = :seniority
                """
            ),
            {"department": student.department, "seniority": student.seniority},
        ).all()
        for row in plan:
            print(f"  {row[0]}")

    finally:
        session.close()
        engine.dispose()
        drop_database()


if __name__ == "__main__":
    main()
