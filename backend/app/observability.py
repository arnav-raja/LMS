"""Logging that is useful once the application is somewhere you cannot
attach a debugger.

Two problems this solves.

The first is that log lines were unstructured text going to stdout, which
a hosted log viewer can store but not search meaningfully. They are JSON
now, so "every 500 in the last hour" is a query rather than a scroll.

The second is worse: a request that failed left a bare traceback with
nothing tying it to who was asking or what they were asking for. Every
line emitted while handling a request now carries the same `request_id`,
and that id goes back to the caller in the `X-Request-ID` header and in
the body of a 500. When somebody reports "it broke", the id they can read
off the screen is enough to find every line the failure produced.
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


# Set per request and read by the formatter. A ContextVar rather than a
# global because requests are handled concurrently.
current_request_id: ContextVar[str | None] = ContextVar(
    "current_request_id", default=None
)

# Attributes LogRecord always carries. Anything else on a record was put
# there deliberately by a caller, so it belongs in the output.
_STANDARD_RECORD_FIELDS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)
            ) + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = current_request_id.get()
        if request_id:
            payload["request_id"] = request_id

        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_FIELDS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # uvicorn installs its own handlers and would otherwise print every
    # line twice, once formatted and once not.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True

    # uvicorn.access already logs every request in its own format, and the
    # middleware below does it properly with timing and a request id.
    logging.getLogger("uvicorn.access").disabled = True


request_logger = logging.getLogger("app.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Gives every request an id, logs how it went, and makes sure a crash
    is recorded rather than swallowed.

    An inbound `X-Request-ID` is honoured, so an id assigned by a load
    balancer or another service stays the same across both.
    """

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        token = current_request_id.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)

            # The only place an unhandled exception is recorded. Without
            # this it reaches the ASGI server as a bare traceback with
            # nothing saying which request produced it.
            request_logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "duration_ms": duration_ms,
                },
            )

            current_request_id.reset(token)

            # The id is in the body as well as the header, because it is
            # the header a person cannot see. Nothing about the error
            # itself is returned — that is for the logs, not the caller.
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Something went wrong on our end.",
                    "request_id": request_id,
                },
                headers={"X-Request-ID": request_id},
            )

        duration_ms = round((time.perf_counter() - started) * 1000, 1)

        request_logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers["X-Request-ID"] = request_id
        current_request_id.reset(token)

        return response
