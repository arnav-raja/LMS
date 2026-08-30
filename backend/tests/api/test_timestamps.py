"""Timestamps written through the API come back as timezone-aware UTC.

The columns are `timestamptz` now, and the code writes `utc_now()`. Before
this, both sides were naive: the values were UTC by convention only, and
nothing in the database or the response said so.
"""

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.models.certificate import Certificate
from app.models.progress import Progress
from app.models.quiz import QuizAttempt


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def assert_recent_utc(value: datetime) -> None:
    assert value.tzinfo is not None, "timestamp came back naive"
    assert value.utcoffset() == timedelta(0)
    assert abs(datetime.now(timezone.utc) - value) < timedelta(minutes=5)


def test_progress_completed_at_is_aware(
    client, db, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    row = (
        db.query(Progress)
        .filter(Progress.user_id == student.id)
        .one()
    )

    assert_recent_utc(row.completed_at)


def test_certificate_issued_at_is_aware(
    client, db, student, student_headers, course_with_content
):
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        complete(client, student_headers, lesson.id)

    certificate = (
        db.query(Certificate)
        .filter(Certificate.user_id == student.id)
        .one()
    )

    assert_recent_utc(certificate.issued_at)


def test_quiz_attempt_submitted_at_is_aware(
    client, db, student, student_headers, course_with_content, make_quiz
):
    for lesson in (course_with_content.lesson_one, course_with_content.lesson_two):
        complete(client, student_headers, lesson.id)

    quiz = make_quiz(course_with_content.chapter_one)
    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()

    client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "option_id": question["options"][0]["id"],
                }
                for question in body["questions"]
            ]
        },
    )

    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == student.id)
        .one()
    )

    assert_recent_utc(attempt.submitted_at)


def test_serialised_timestamps_carry_an_offset(
    client, student_headers, course_with_content
):
    """A client reading the JSON must be able to tell what zone it is in."""
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        complete(client, student_headers, lesson.id)

    issued_at = client.get(
        "/certificates/me", headers=student_headers
    ).json()[0]["issued_at"]

    parsed = datetime.fromisoformat(issued_at)
    assert parsed.tzinfo is not None
