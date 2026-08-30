"""Request ids, structured logs, and a health check that means something.

None of this changes what the application does. It changes whether you
can find out what it did, once it is running somewhere you cannot attach
a debugger to.
"""

import json
import logging

import pytest

from fastapi import APIRouter

from app.main import app as fastapi_app
from app.observability import JsonFormatter
from app.observability import current_request_id


# ------------------------------------------------------------ formatter --

def format_record(**kwargs) -> dict:
    record = logging.LogRecord(
        name=kwargs.pop("name", "app.test"),
        level=kwargs.pop("level", logging.INFO),
        pathname=__file__,
        lineno=1,
        msg=kwargs.pop("msg", "something happened"),
        args=(),
        exc_info=kwargs.pop("exc_info", None),
    )

    for key, value in kwargs.items():
        setattr(record, key, value)

    return json.loads(JsonFormatter().format(record))


def test_a_log_line_is_one_json_object():
    line = format_record()

    assert line["level"] == "INFO"
    assert line["logger"] == "app.test"
    assert line["message"] == "something happened"
    assert line["time"].endswith("Z")


def test_extra_fields_are_included():
    """This is what makes the logs queryable — "every request slower than
    a second" needs duration to be a field, not part of a sentence."""
    line = format_record(method="GET", path="/courses", status=200, duration_ms=4.2)

    assert line["method"] == "GET"
    assert line["path"] == "/courses"
    assert line["status"] == 200
    assert line["duration_ms"] == 4.2


def test_the_request_id_is_attached_when_one_is_set():
    token = current_request_id.set("abc123")
    try:
        assert format_record()["request_id"] == "abc123"
    finally:
        current_request_id.reset(token)


def test_there_is_no_request_id_outside_a_request():
    assert "request_id" not in format_record()


def test_a_traceback_is_captured():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        line = format_record(exc_info=sys.exc_info())

    assert "ValueError: boom" in line["exception"]


def test_unserialisable_values_do_not_break_the_line():
    """A log line must never be the thing that raises."""
    line = format_record(thing=object())

    assert "thing" in line


# ----------------------------------------------------------- request ids --

def test_every_response_carries_a_request_id(client):
    response = client.get("/health")

    assert response.headers["X-Request-ID"]


def test_each_request_gets_its_own_id(client):
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]

    assert first != second


def test_an_inbound_request_id_is_honoured(client):
    """So an id assigned by a load balancer stays the same across both."""
    response = client.get("/health", headers={"X-Request-ID": "from-upstream"})

    assert response.headers["X-Request-ID"] == "from-upstream"


def test_errors_carry_a_request_id_too(client, student_headers):
    response = client.get("/admin/dashboard", headers=student_headers)

    assert response.status_code == 403
    assert response.headers["X-Request-ID"]


def test_the_browser_is_allowed_to_read_the_header(client):
    """Pointless to return it if the frontend cannot see it — CORS hides
    every header that is not explicitly exposed."""
    response = client.get(
        "/health", headers={"Origin": "http://localhost:5173"}
    )

    exposed = response.headers.get("access-control-expose-headers", "")
    assert "X-Request-ID" in exposed


# ------------------------------------------------- unhandled exceptions --

@pytest.fixture
def exploding_route():
    """A route that raises, to check what happens when something genuinely
    unexpected goes wrong."""
    router = APIRouter()

    @router.get("/__boom__")
    def boom():
        raise RuntimeError("something nobody planned for")

    fastapi_app.include_router(router)
    yield
    fastapi_app.router.routes = [
        route
        for route in fastapi_app.router.routes
        if getattr(route, "path", None) != "/__boom__"
    ]


def test_a_crash_returns_a_request_id_the_user_can_quote(
    client, exploding_route, caplog
):
    with caplog.at_level(logging.ERROR):
        response = client.get("/__boom__")

    assert response.status_code == 500
    body = response.json()

    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["detail"] == "Something went wrong on our end."


def test_a_crash_does_not_leak_the_exception_to_the_caller(
    client, exploding_route, caplog
):
    with caplog.at_level(logging.ERROR):
        response = client.get("/__boom__")

    assert "something nobody planned for" not in response.text
    assert "Traceback" not in response.text


def test_a_crash_is_logged_with_its_traceback(client, exploding_route, caplog):
    with caplog.at_level(logging.ERROR):
        client.get("/__boom__")

    failures = [r for r in caplog.records if r.message == "request failed"]

    assert len(failures) == 1
    assert failures[0].path == "/__boom__"
    assert failures[0].status == 500
    assert failures[0].exc_info is not None


# ------------------------------------------------------------- health ----

def test_health_reports_the_database(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "running", "database": "ok"}


def test_health_fails_when_the_database_cannot_be_reached(client, db, caplog):
    """The point of the change. It used to answer "running"
    unconditionally, so an uptime monitor stayed green through exactly the
    outage it exists to catch."""
    def explode(*args, **kwargs):
        raise RuntimeError("connection refused")

    original = db.execute
    db.execute = explode

    try:
        with caplog.at_level(logging.ERROR):
            response = client.get("/health")
    finally:
        db.execute = original

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": "unreachable",
    }
