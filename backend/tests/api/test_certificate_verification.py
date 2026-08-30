"""The public certificate check.

`certificate_number` has been generated on every certificate since they
existed, printed in the app, and verifiable by nothing. Somebody handed
one had no way to confirm it without an account here — which is the whole
point of a certificate.

This is the only unauthenticated route in the application, so what it
does *not* return matters as much as what it does.
"""


def complete(client, headers, subchapter_id):
    return client.post(
        "/progress/complete",
        headers=headers,
        json={"subchapter_id": subchapter_id},
    )


def earn_a_certificate(client, headers, content):
    for lesson in (content.lesson_one, content.lesson_two, content.lesson_three):
        complete(client, headers, lesson.id)

    return client.get("/certificates/me", headers=headers).json()[0]


def test_a_real_number_verifies(
    client, student, student_headers, course_with_content
):
    certificate = earn_a_certificate(client, student_headers, course_with_content)

    response = client.get(f"/verify/{certificate['certificate_number']}")

    assert response.status_code == 200
    body = response.json()
    assert body["holder_name"] == student.name
    assert body["course_title"] == "Security Basics"
    assert body["certificate_number"] == certificate["certificate_number"]
    assert body["issued_at"]


def test_verifying_needs_no_account(
    client, student_headers, course_with_content
):
    """The point of the route. A recruiter or auditor holding a
    certificate has no login here."""
    certificate = earn_a_certificate(client, student_headers, course_with_content)

    # No Authorization header at all.
    response = client.get(f"/verify/{certificate['certificate_number']}")

    assert response.status_code == 200


def test_it_reveals_nothing_beyond_the_certificate(
    client, student_headers, course_with_content
):
    """Unauthenticated, so it carries only what the certificate itself
    already claims — not the holder's email, account id, department, or
    anything about their scores."""
    certificate = earn_a_certificate(client, student_headers, course_with_content)

    body = client.get(f"/verify/{certificate['certificate_number']}").json()

    assert set(body) == {
        "certificate_number",
        "holder_name",
        "course_title",
        "issued_at",
    }


def test_an_unknown_number_is_not_found(client):
    response = client.get("/verify/ARNAV-DOESNOTEXIST")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No certificate found with that number"
    }


def test_a_malformed_number_answers_the_same_way(client):
    """A caller must not be able to tell "wrong shape" from "no such
    certificate" — that would say something about how numbers are made."""
    unknown = client.get("/verify/ARNAV-DOESNOTEXIST")
    nonsense = client.get("/verify/not-a-certificate-number-at-all")

    assert nonsense.status_code == unknown.status_code
    assert nonsense.json() == unknown.json()


def test_surrounding_whitespace_is_tolerated(
    client, student_headers, course_with_content
):
    """People paste these out of emails and PDFs."""
    certificate = earn_a_certificate(client, student_headers, course_with_content)

    response = client.get(f"/verify/  {certificate['certificate_number']}  ")

    assert response.status_code == 200


def test_a_revoked_account_takes_its_certificate_with_it(
    client, admin_headers, student, student_headers, course_with_content
):
    """Deleting an account cascades its certificates away, so the number
    on a certificate belonging to a deleted person stops verifying."""
    certificate = earn_a_certificate(client, student_headers, course_with_content)

    client.delete(f"/admin/users/{student.id}", headers=admin_headers)

    response = client.get(f"/verify/{certificate['certificate_number']}")

    assert response.status_code == 404
