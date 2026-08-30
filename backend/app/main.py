from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ALLOWED_ORIGINS
from app.errors import DomainError

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


app = FastAPI(
    title="Arnav LMS",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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
def health():
    return {
        "status": "running"
    }