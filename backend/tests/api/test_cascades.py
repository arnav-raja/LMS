"""Deleting an account or a course removes what belonged to it.

Six foreign keys had no ON DELETE behaviour. Deleting a student who had
ever taken a quiz failed outright — the database refused, and the admin
was told only that they "may still have related records", with no way to
proceed. These tests cover both halves: that the delete now succeeds, and
that it does not leave orphaned rows behind.
"""

from app.models.certificate import Certificate
from app.models.chapter import Chapter
from app.models.course_access_rule import CourseAccessRule
from app.models.progress import Progress
from app.models.quiz import Quiz
from app.models.quiz import QuizAttempt
from app.models.subchapter import Subchapter


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def finish_the_course(client, headers, content):
    for lesson in (content.lesson_one, content.lesson_two, content.lesson_three):
        complete(client, headers, lesson.id)


def test_deleting_a_student_with_a_full_history_succeeds(
    client, db, admin_headers, student, student_headers, course_with_content,
    make_quiz
):
    """This is exactly the case that used to be impossible."""
    quiz = make_quiz(course_with_content.chapter_one)
    complete(client, student_headers, course_with_content.lesson_one.id)
    complete(client, student_headers, course_with_content.lesson_two.id)

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
    complete(client, student_headers, course_with_content.lesson_three.id)

    student_id = student.id

    response = client.delete(
        f"/admin/users/{student_id}", headers=admin_headers
    )

    assert response.status_code == 200

    removed = response.json()["removed"]
    assert removed["progress"] == 3
    assert removed["quiz_attempts"] == 1
    assert removed["certificates"] == 1

    db.expire_all()
    assert (
        db.query(Progress).filter(Progress.user_id == student_id).count() == 0
    )
    assert (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == student_id)
        .count()
        == 0
    )
    assert (
        db.query(Certificate)
        .filter(Certificate.user_id == student_id)
        .count()
        == 0
    )


def test_delete_reports_nothing_removed_for_an_untouched_account(
    client, admin_headers, student
):
    response = client.delete(f"/admin/users/{student.id}", headers=admin_headers)

    assert response.json()["removed"] == {
        "progress": 0,
        "quiz_attempts": 0,
        "certificates": 0,
    }


def test_deleting_a_student_leaves_other_students_alone(
    client, db, admin_headers, student, student_headers, other_student,
    headers_for, course_with_content, grant_access
):
    grant_access(course_with_content.course, department="FI", seniority="Junior")

    complete(client, student_headers, course_with_content.lesson_one.id)
    complete(client, headers_for(other_student), course_with_content.lesson_one.id)

    survivor_id = other_student.id
    client.delete(f"/admin/users/{student.id}", headers=admin_headers)

    db.expire_all()
    assert (
        db.query(Progress).filter(Progress.user_id == survivor_id).count() == 1
    )


def test_deleting_a_course_removes_its_whole_tree(
    client, db, admin_headers, student_headers, course_with_content, make_quiz
):
    course_id = course_with_content.course.id
    chapter_ids = [
        course_with_content.chapter_one.id,
        course_with_content.chapter_two.id,
    ]

    make_quiz(course_with_content.chapter_one)
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.delete(
        f"/admin/courses/{course_id}", headers=admin_headers
    )
    assert response.status_code == 200

    db.expire_all()
    assert (
        db.query(Chapter).filter(Chapter.course_id == course_id).count() == 0
    )
    assert (
        db.query(Subchapter)
        .filter(Subchapter.chapter_id.in_(chapter_ids))
        .count()
        == 0
    )
    assert (
        db.query(Quiz).filter(Quiz.chapter_id.in_(chapter_ids)).count() == 0
    )
    assert (
        db.query(CourseAccessRule)
        .filter(CourseAccessRule.course_id == course_id)
        .count()
        == 0
    )


def test_deleting_a_course_removes_the_progress_recorded_against_it(
    client, db, admin_headers, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)
    student_id = student.id

    client.delete(
        f"/admin/courses/{course_with_content.course.id}", headers=admin_headers
    )

    db.expire_all()
    assert (
        db.query(Progress).filter(Progress.user_id == student_id).count() == 0
    )


def test_deleting_a_course_removes_its_certificates(
    client, db, admin_headers, student, student_headers, course_with_content
):
    finish_the_course(client, student_headers, course_with_content)
    student_id = student.id

    assert len(client.get("/certificates/me", headers=student_headers).json()) == 1

    client.delete(
        f"/admin/courses/{course_with_content.course.id}", headers=admin_headers
    )

    db.expire_all()
    assert (
        db.query(Certificate)
        .filter(Certificate.user_id == student_id)
        .count()
        == 0
    )


def test_deleting_a_quiz_removes_its_attempts(
    client, db, admin_headers, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)
    quiz_id = quiz.id

    complete(client, student_headers, course_with_content.lesson_one.id)
    complete(client, student_headers, course_with_content.lesson_two.id)

    body = client.get(f"/quizzes/{quiz_id}", headers=student_headers).json()
    client.post(
        f"/quizzes/{quiz_id}/submit",
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

    client.delete(f"/admin/quizzes/{quiz_id}", headers=admin_headers)

    db.expire_all()
    assert (
        db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).count() == 0
    )
