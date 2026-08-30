import os

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised at import time when a required setting is missing.

    Deliberately fatal. A missing SECRET_KEY used to let the app start
    normally and then fail on the first login attempt with an error from
    deep inside the JWT library; a missing DATABASE_URL failed with an
    AttributeError on None. Both are configuration mistakes, and both are
    far cheaper to find at startup than in production traffic.
    """


def _required(name: str, hint: str) -> str:
    value = os.getenv(name)

    if not value or not value.strip():
        raise ConfigError(
            f"{name} is not set. {hint}\n"
            "Copy .env.example to .env for local development, or set it in "
            "your host's environment for a deployment."
        )

    return value.strip()


DATABASE_URL = _required(
    "DATABASE_URL",
    "It is the full connection string for the PostgreSQL database, "
    "e.g. postgresql://user:password@host:5432/database.",
)

SECRET_KEY = _required(
    "SECRET_KEY",
    "It is the secret every access token is signed with, so it must be a "
    "long random string and must stay the same across restarts — changing "
    "it signs everyone out.",
)

# Unlike the two above, this one has a sensible universal default. It is
# still read from the environment so it can be changed without a code edit.
ALGORITHM = os.getenv("ALGORITHM", "HS256").strip() or "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "30"
    )
)

# How much the application logs. INFO records one line per request;
# WARNING quietens that down to problems only.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"

# Comma-separated list of frontend origins allowed to call this API, e.g.
# "http://localhost:5173,https://app.arnav.com". Falls back to the two
# local dev servers if not set, so nothing breaks for local development.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if origin.strip()
]
