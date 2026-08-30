"""Reports have to leave the application.

Every one of these is something a compliance or HR person eventually needs
in a spreadsheet. Reading it off the screen and retyping it was the
alternative.
"""

import csv
import io

import pytest

from app.services.csv_export import safe_filename


def read_csv(response):
    """Parse a CSV response back into header and rows, stripping the BOM
    that is there for Excel's benefit."""
    text = response.text.lstrip("﻿")
    rows = list(csv.reader(io.StringIO(text)))
    return rows[0], rows[1:]


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


# ------------------------------------------------------------- filenames --

@pytest.mark.parametrize(
    "given, expected",
    [
        ("Fire Safety roster.csv", "Fire Safety roster.csv"),
        # A title is typed by an admin, so it can contain anything that
        # would otherwise break out of the Content-Disposition header.
        ('Evil"; rm -rf /.csv', "Evil-- rm -rf -.csv"),
        ('Quote" injection.csv', "Quote- injection.csv"),
        ("Line\nbreak.csv", "Line-break.csv"),
        # Header values encode as latin-1, so anything outside ASCII would
        # raise while building the response rather than merely look odd.
        ("Sicherheit für Alle.csv", "Sicherheit f-r Alle.csv"),
        ("安全講習.csv", "----.csv"),
        ("", "export"),
        ("...", "export"),
    ],
)
def test_filenames_cannot_break_the_header(given, expected):
    assert safe_filename(given) == expected


def test_filenames_are_always_encodable_as_a_header():
    """The actual requirement behind the ASCII rule."""
    for title in ("安全講習", "Sicherheit für Alle", "Zażółć gęślą jaźń"):
        safe_filename(title).encode("latin-1")


def test_filenames_are_length_capped():
    assert len(safe_filename("x" * 500)) == 100


# ---------------------------------------------------------------- roster --

def test_roster_csv_contains_the_students(
    client, admin_headers, student, student_headers, course_with_content
):
    complete(client, student_headers, course_with_content.lesson_one.id)

    response = client.get(
        f"/admin/courses/{course_with_content.course.id}/students.csv",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    header, rows = read_csv(response)
    assert header[0] == "Name"
    assert len(rows) == 1
    assert rows[0][0] == student.name
    assert rows[0][4] == "1"   # lessons completed
    assert rows[0][5] == "3"   # lessons total


def test_roster_csv_is_named_after_the_course(
    client, admin_headers, course_with_content
):
    response = client.get(
        f"/admin/courses/{course_with_content.course.id}/students.csv",
        headers=admin_headers,
    )

    assert "Security Basics roster.csv" in response.headers["content-disposition"]


def test_a_comma_in_a_name_does_not_shift_the_columns(
    client, admin_headers, make_user, course_with_content
):
    """The reason this uses the csv module rather than joining commas."""
    make_user(
        name='Ada "Countess" Lovelace, Jr',
        username="ada2",
        email="ada2@example.com",
        department="EC",
        seniority="Mid",
    )

    response = client.get(
        f"/admin/courses/{course_with_content.course.id}/students.csv",
        headers=admin_headers,
    )

    header, rows = read_csv(response)
    tricky = next(r for r in rows if r[0].startswith("Ada "))

    assert tricky[0] == 'Ada "Countess" Lovelace, Jr'
    assert len(tricky) == len(header)


def test_roster_csv_is_admin_only(client, student_headers, course_with_content):
    response = client.get(
        f"/admin/courses/{course_with_content.course.id}/students.csv",
        headers=student_headers,
    )

    assert response.status_code == 403


def test_roster_csv_404s_for_an_unknown_course(client, admin_headers):
    assert (
        client.get(
            "/admin/courses/999999/students.csv", headers=admin_headers
        ).status_code
        == 404
    )


# --------------------------------------------------------- quiz results --

def test_quiz_results_csv_records_the_version_attempted(
    client, admin_headers, student, student_headers, course_with_content,
    make_quiz
):
    """A quiz can be edited without erasing past attempts, so an export
    has to say which version a result was earned against."""
    quiz = make_quiz(course_with_content.chapter_one)

    for lesson in (course_with_content.lesson_one, course_with_content.lesson_two):
        complete(client, student_headers, lesson.id)

    body = client.get(f"/quizzes/{quiz.id}", headers=student_headers).json()
    client.post(
        f"/quizzes/{quiz.id}/submit",
        headers=student_headers,
        json={
            "answers": [
                {"question_id": q["id"], "option_id": q["options"][0]["id"]}
                for q in body["questions"]
            ]
        },
    )

    response = client.get(
        f"/admin/quizzes/{quiz.id}/results.csv", headers=admin_headers
    )

    assert response.status_code == 200
    header, rows = read_csv(response)

    assert header == [
        "Name",
        "Attempts",
        "Best score",
        "Passed",
        "Version attempted",
        "Current version",
    ]
    assert rows[0][0] == student.name
    assert rows[0][2] == "100.0"
    assert rows[0][3] == "TRUE"
    assert rows[0][4] == "1"


def test_quiz_results_csv_is_admin_only(
    client, student_headers, course_with_content, make_quiz
):
    quiz = make_quiz(course_with_content.chapter_one)

    assert (
        client.get(
            f"/admin/quizzes/{quiz.id}/results.csv", headers=student_headers
        ).status_code
        == 403
    )


# --------------------------------------------------------- certificates --

def test_certificate_registry_csv(
    client, admin_headers, student, student_headers, course_with_content
):
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        complete(client, student_headers, lesson.id)

    response = client.get("/admin/certificates.csv", headers=admin_headers)

    assert response.status_code == 200
    header, rows = read_csv(response)

    assert header[0] == "Certificate number"
    assert len(rows) == 1
    assert rows[0][0].startswith("ARNAV-")
    assert rows[0][1] == student.name
    assert rows[0][3] == "Security Basics"


def test_certificate_csv_can_be_filtered_by_course(
    client, admin_headers, student_headers, course_with_content, make_course
):
    for lesson in (
        course_with_content.lesson_one,
        course_with_content.lesson_two,
        course_with_content.lesson_three,
    ):
        complete(client, student_headers, lesson.id)

    other = make_course(title="Unrelated")

    matching = client.get(
        f"/admin/certificates.csv?course_id={course_with_content.course.id}",
        headers=admin_headers,
    )
    non_matching = client.get(
        f"/admin/certificates.csv?course_id={other.id}", headers=admin_headers
    )

    assert len(read_csv(matching)[1]) == 1
    assert len(read_csv(non_matching)[1]) == 0


def test_certificate_csv_is_admin_only(client, student_headers):
    assert (
        client.get("/admin/certificates.csv", headers=student_headers).status_code
        == 403
    )


def test_an_empty_export_still_has_its_header(client, admin_headers):
    """A spreadsheet with no rows must still open as a spreadsheet."""
    response = client.get("/admin/certificates.csv", headers=admin_headers)

    header, rows = read_csv(response)
    assert header[0] == "Certificate number"
    assert rows == []
