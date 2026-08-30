import logging

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import ALLOWED_ORIGINS
from app.config import LOG_LEVEL
from app.database import get_db
from app.errors import DomainError
from app.observability import RequestContextMiddleware
from app.observability import configure_logging

from app.routers.auth import router as auth_router
from app.routers.course import router as course_router
from app.routers.chapter import router as chapter_router
from app.routers.access import router as access_router
from app.routers.progress import router as progress_router
from app.routers.learning import router as learning_router
from app.routers.admin import router as admin_router
from app.routers.dashboard import router as dashboard_router
from app.routers.course_builder import router as course_builder_router
from app.routers.quiz import router as quiz_router
from app.routers.certificate import router as certificate_router


configure_logging(LOG_LEVEL)

app = FastAPI(
    title="Arnav LMS",
    version="1.0.0"
)


# Order matters. Middleware runs outermost-first in the reverse of the
# order it is added, so the request context has to be added last to wrap
# CORS — otherwise a request rejected by CORS would carry no request id.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # So a browser can read the id off a failed response and a person can
    # quote it when reporting the failure.
    expose_headers=["X-Request-ID"],
)

app.add_middleware(RequestContextMiddleware)


@app.exception_handler(DomainError)
def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
    """Turns any deliberate application error into its HTTP response.

    `{"detail": ...}` matches the shape FastAPI's own HTTPException
    produces, so every client keeps reading errors the same way.
    """
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
    )


app.include_router(auth_router)
app.include_router(course_router)
app.include_router(chapter_router)
app.include_router(access_router)
app.include_router(progress_router)
app.include_router(learning_router)
app.include_router(admin_router)
app.include_router(dashboard_router)
app.include_router(course_builder_router)
app.include_router(quiz_router)
app.include_router(certificate_router)


@app.get("/")
def home():
    return {
        "message": "Arnav LMS API"
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Whether the application can actually serve a request.

    This used to return "running" unconditionally, which meant it went on
    reporting healthy while the database was unreachable — so an uptime
    monitor watching it stayed green through exactly the outage it exists
    to catch, and a platform health check would never restart or roll back
    a deployment that could not talk to its database.

    Answers 503 when the database cannot be reached, which is what makes
    it usable as a real health check.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception as error:
        logging.getLogger("app.health").error(
            "health check failed", extra={"reason": str(error)}
        )

        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "unreachable"},
        )

    return {
        "status": "running",
        "database": "ok",
    }