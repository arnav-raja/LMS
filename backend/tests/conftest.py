import os

# Must be set before anything imports app.config, so tests never touch the
# real database or secret configured in a developer's .env file.
#
# Tests run against a real PostgreSQL database, because PostgreSQL is what
# production runs. SQLite does not enforce foreign keys unless explicitly
# switched on, so a missing cascade would pass here and fail in production —
# exactly the class of bug these tests exist to catch.
#
# Start one with:  docker compose --profile test up -d test-db
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://lms_test:lms_test@localhost:55432/lms_test",
)

# Forced, not merely defaulted. A developer with DATABASE_URL exported in
# their shell must not have the suite point at that database, because the
# fixtures below drop and recreate every table.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401 — registers every model on Base.metadata


def _guard_against_a_real_database(url: str) -> None:
    """The engine fixture drops every table. Refuse to do that to anything
    that is not obviously a throwaway test database."""
    database_name = url.rsplit("/", 1)[-1].split("?")[0]

    if "test" not in database_name.lower():
        raise RuntimeError(
            f"Refusing to run the suite against database {database_name!r}: "
            "the test fixtures drop every table, so the database name must "
            "contain 'test'. Set TEST_DATABASE_URL to a throwaway database."
        )


@pytest.fixture(scope="session")
def engine():
    """One engine and one schema build for the whole run."""
    _guard_against_a_real_database(TEST_DATABASE_URL)

    engine = create_engine(TEST_DATABASE_URL)

    # Dropped first as well as last, so a run that was killed part-way
    # through does not leave the next one with a stale schema.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(engine):
    """A session inside a transaction that is rolled back when the test ends.

    This is what makes a real database affordable: the schema is built once
    per run rather than once per test, and each test still starts clean.

    `join_transaction_mode="create_savepoint"` is the important part — the
    application code under test calls `commit()` freely, and that must
    release a savepoint rather than end the outer transaction, or the
    rollback below would have nothing left to undo.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
