"""Shared fixtures for the HTTP-level route tests.

These drive the real FastAPI app through a client, so mistakes that live in
the router layer — a wrong service call, a missing auth check, a wrong
status code — fail here. The unit tests in tests/ call services directly
and are blind to all of it.

The app and the test share one Session, handed to the app by overriding
`get_db`. That keeps rows written by a fixture visible to the request under
test, and rows written by the request visible to the assertions after it.
"""

import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers every model on Base.metadata

from app.database import Base
from app.database import get_db
from app.main import app as fastapi_app

from app.models.chapter import Chapter
from app.models.course import Course
from app.models.course_access_rule import CourseAccessRule
from app.models.quiz import Quiz
from app.models.quiz import QuizOption
from app.models.quiz import QuizQuestion
from app.models.subchapter import Subchapter
from app.models.user import User

from app.services.jwt_service import create_access_token
from app.utils.security import hash_password


PASSWORD = "correct-horse-battery"

# bcrypt is deliberately slow. Hash the shared test password once for the
# whole run rather than once per user per test.
_PASSWORD_HASH = hash_password(PASSWORD)


@pytest.fixture
def db():
    """A session against a fresh in-memory database, one per test.

    StaticPool keeps every connection pointed at the same in-memory
    database — without it, SQLite would hand out a new empty one each time.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db):
    def override_get_db():
        # Deliberately not closed here — the `db` fixture owns its lifetime,
        # and the test still needs it after the response comes back.
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()


# ------------------------------------------------------------- identities --

def auth_headers(user: User) -> dict:
    """A bearer header for this user, minted the same way login does."""
    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user(db):
    def _make(
        name="Ada Lovelace",
        username="ada",
        email="ada@example.com",
        role="student",
        department="EC",
        seniority="Mid",
    ):
        user = User(
            name=name,
            username=username,
            email=email,
            password_hash=_PASSWORD_HASH,
            role=role,
            department=department,
            seniority=seniority,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture
def admin(make_user):
    return make_user(
        name="Grace Hopper",
        username="grace",
        email="grace@example.com",
        role="admin",
        department=None,
        seniority=None,
    )


@pytest.fixture
def student(make_user):
    return make_user()


@pytest.fixture
def other_student(make_user):
    """A second student in a different department, for access tests."""
    return make_user(
        name="Alan Turing",
        username="alan",
        email="alan@example.com",
        department="FI",
        seniority="Junior",
    )


@pytest.fixture
def password():
    """The plaintext password every fixture user is created with."""
    return PASSWORD


@pytest.fixture
def headers_for():
    """Bearer headers for an arbitrary user, for tests that need an
    identity beyond the standard `admin` / `student` pair."""
    return auth_headers


@pytest.fixture
def admin_headers(admin):
    return auth_headers(admin)


@pytest.fixture
def student_headers(student):
    return auth_headers(student)


# -------------------------------------------------------------- content ----

@pytest.fixture
def make_course(db):
    def _make(title="Security Basics", status="published", description="Intro"):
        course = Course(
            title=title,
            description=description,
            status=status,
            num_chapters=0,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    return _make


@pytest.fixture
def make_chapter(db):
    def _make(course, chapter_number=1, title="Chapter One"):
        chapter = Chapter(
            course_id=course.id,
            chapter_number=chapter_number,
            title=title,
            description="A chapter",
            num_subchapters=0,
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)

        course.num_chapters = (
            db.query(Chapter).filter(Chapter.course_id == course.id).count()
        )
        db.commit()
        return chapter

    return _make


@pytest.fixture
def make_subchapter(db):
    def _make(chapter, subchapter_number=1, title="Lesson One", content="Body text"):
        subchapter = Subchapter(
            chapter_id=chapter.id,
            subchapter_number=subchapter_number,
            title=title,
            content=content,
        )
        db.add(subchapter)
        db.commit()
        db.refresh(subchapter)

        chapter.num_subchapters = (
            db.query(Subchapter)
            .filter(Subchapter.chapter_id == chapter.id)
            .count()
        )
        db.commit()
        return subchapter

    return _make


@pytest.fixture
def make_quiz(db):
    def _make(chapter, title="Chapter One Quiz", passing_score=70, questions=2):
        quiz = Quiz(
            chapter_id=chapter.id,
            title=title,
            passing_score=passing_score,
        )
        db.add(quiz)
        db.flush()

        for number in range(1, questions + 1):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_number=number,
                question_text=f"Question {number}?",
            )
            db.add(question)
            db.flush()

            db.add(
                QuizOption(
                    question_id=question.id,
                    option_text="Right",
                    is_correct=True,
                )
            )
            db.add(
                QuizOption(
                    question_id=question.id,
                    option_text="Wrong",
                    is_correct=False,
                )
            )

        db.commit()
        db.refresh(quiz)
        return quiz

    return _make


@pytest.fixture
def grant_access(db):
    def _grant(course, department="EC", seniority="Mid"):
        rule = CourseAccessRule(
            course_id=course.id,
            department=department,
            seniority=seniority,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    return _grant


@pytest.fixture
def course_with_content(make_course, make_chapter, make_subchapter, grant_access):
    """A published two-chapter course the default `student` can reach.

    Chapter 1 has two lessons, chapter 2 has one. Returned as a small
    namespace so tests can reach any piece without rebuilding it.
    """

    class Content:
        pass

    content = Content()
    content.course = make_course()
    content.chapter_one = make_chapter(content.course, 1, "Chapter One")
    content.chapter_two = make_chapter(content.course, 2, "Chapter Two")
    content.lesson_one = make_subchapter(content.chapter_one, 1, "Lesson One")
    content.lesson_two = make_subchapter(content.chapter_one, 2, "Lesson Two")
    content.lesson_three = make_subchapter(content.chapter_two, 1, "Lesson Three")
    grant_access(content.course)
    return content
