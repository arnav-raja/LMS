"""The migrations must build the same schema the models describe.

Nothing else checks this. The test suite builds its schema with
`create_all()` straight from the models, while production only ever gets
what the migrations produce — so a model edited without a matching
migration passes every other test in this suite and then fails on deploy,
or worse, quietly runs against a column of the wrong type.

This test runs the whole migration chain against an empty database and
asks Alembic to diff the result against the models.
"""

import os

import pytest

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext

from sqlalchemy import create_engine
from sqlalchemy import text

from app.database import Base

from tests.conftest import TEST_DATABASE_URL


MIGRATION_DATABASE = "lms_migration_check"


def _server_url() -> str:
    """The same server as the test database, but pointed at `postgres` so
    the throwaway database can be created and dropped."""
    return TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"


@pytest.fixture
def migrated_engine():
    admin_engine = create_engine(_server_url(), isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP DATABASE IF EXISTS "{MIGRATION_DATABASE}"')
            )
            connection.execute(text(f'CREATE DATABASE "{MIGRATION_DATABASE}"'))
    except Exception as error:  # pragma: no cover - environment dependent
        admin_engine.dispose()
        pytest.skip(f"Cannot create a scratch database here: {error}")

    url = TEST_DATABASE_URL.rsplit("/", 1)[0] + f"/{MIGRATION_DATABASE}"

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))

    # alembic/env.py deliberately lets DATABASE_URL win over alembic.ini, so
    # that one project can migrate a different database per environment.
    # That means setting the URL on the config alone is not enough here —
    # without this, the chain would run against the main test database.
    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url

    try:
        command.upgrade(config, "head")
    finally:
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url

    engine = create_engine(url)

    try:
        yield engine
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(f'DROP DATABASE IF EXISTS "{MIGRATION_DATABASE}"')
            )
        admin_engine.dispose()


def test_migrations_produce_the_schema_the_models_describe(migrated_engine):
    with migrated_engine.connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, Base.metadata)

    assert differences == [], (
        "The migrations and the models disagree. Each entry below is "
        "something the models declare that the migrations do not produce, "
        "or the other way round:\n"
        + "\n".join(f"  - {difference}" for difference in differences)
    )


def test_timestamp_columns_are_timezone_aware_after_migrating(migrated_engine):
    """Called out separately because it is the change most likely to be
    silently reverted: dropping `timezone=True` from a model still passes
    every behavioural test on a fresh database."""
    with migrated_engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT table_name, column_name, data_type
                  FROM information_schema.columns
                 WHERE column_name IN
                       ('completed_at', 'issued_at', 'submitted_at')
                """
            )
        ).all()

    assert rows, "expected timestamp columns to exist"

    for table_name, column_name, data_type in rows:
        assert data_type == "timestamp with time zone", (
            f"{table_name}.{column_name} is {data_type}, "
            "so it has lost its timezone"
        )
