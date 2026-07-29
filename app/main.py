from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS

from app.routers.auth import router as auth_router
from app.routers.course import router as course_router
from app.routers.chapter import router as chapter_router
from app.routers.access import router as access_router
from app.routers.progress import router as progress_router
from app.routers.learning import router as learning_router
from app.routers.admin import router as admin_router
from app.routers.dashboard import router as dashboard_router
from app.routers.course_builder import router as course_builder_router
from app.routers.organisation import router as organisation_router
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


app.include_router(auth_router)
app.include_router(course_router)
app.include_router(chapter_router)
app.include_router(access_router)
app.include_router(progress_router)
app.include_router(learning_router)
app.include_router(admin_router)
app.include_router(dashboard_router)
app.include_router(course_builder_router)
app.include_router(organisation_router)
app.include_router(quiz_router)
app.include_router(certificate_router)


@app.on_event("startup")
def allow_verified_custom_domain():
    """If an organisation has a verified custom domain, the frontend
    served from it also needs to be allowed to call this API."""
    from app.database import SessionLocal
    from app.services.organisation_service import get_or_create_organisation

    db = SessionLocal()

    try:
        organisation = get_or_create_organisation(db)

        if organisation.domain_verified and organisation.custom_domain:
            for scheme in ("https://", "http://"):
                origin = f"{scheme}{organisation.custom_domain}"

                if origin not in ALLOWED_ORIGINS:
                    ALLOWED_ORIGINS.append(origin)
    finally:
        db.close()


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