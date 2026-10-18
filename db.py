"""
dbsync database helpers.

Wraps psycopg2 with:

- connect()             - open a connection to Aiven
- test_connection()     - ping and return the latency
- query() / execute()   - run SQL, return rows
- get_alembic_version() - read the current schema version
- list_tables()         - list all tables in public schema
- count_rows()          - row count for a table
"""

import time
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config


# =========================================================
# CONNECTION
# =========================================================

@contextmanager
def connect(config: Config):
    """
    Context manager: open a connection to Aiven and
    ensure it is closed.

    Usage:
        with connect(cfg) as conn:
            ...
    """
    conn = psycopg2.connect(
        config.uri(),
        connect_timeout=config.timeout,
    )
    try:
        yield conn
    finally:
        conn.close()


def test_connection(config: Config) -> tuple[bool, int, str]:
    """
    Check whether Aiven is reachable.

    Returns (ok, elapsed_ms, detail).
    """
    t0 = time.perf_counter()

    try:
        conn = psycopg2.connect(
            config.uri(),
            connect_timeout=config.timeout,
        )
        elapsed = int((time.perf_counter() - t0) * 1000)

        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()

        return True, elapsed, "OK"

    except psycopg2.OperationalError as e:
        elapsed = int((time.perf_counter() - t0) * 1000)
        return False, elapsed, str(e).strip().splitlines()[0]

    except Exception as e:
        elapsed = int((time.perf_counter() - t0) * 1000)
        return False, elapsed, str(e)


# =========================================================
# QUERIES
# =========================================================

def query(config: Config, sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT and return rows as list of dicts."""
    with connect(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


def execute(config: Config, sql: str, params: tuple = ()) -> int:
    """Run a non-SELECT and return affected row count."""
    with connect(config) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount


# =========================================================
# SCHEMA INSPECTION
# =========================================================

def get_alembic_version(config: Config) -> str | None:
    """Return the current migration head, or None."""
    try:
        rows = query(
            config,
            "SELECT version_num FROM alembic_version LIMIT 1;",
        )
        if rows:
            return rows[0]["version_num"]
        return None
    except psycopg2.errors.UndefinedTable:
        return None


def list_tables(config: Config) -> list[str]:
    """Return the names of all tables in the public schema."""
    rows = query(
        config,
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """,
    )
    return [r["tablename"] for r in rows]


def count_rows(config: Config, table: str) -> int:
    """Return the row count of a table."""
    # Table name is interpolated (not parameterised) because
    # SQL does not allow a placeholder for an identifier.
    # We constrain it to a strict allowlist pattern to
    # prevent injection.
    if not table.replace("_", "").isalnum():
        raise ValueError(f"Invalid table name: {table}")

    rows = query(config, f'SELECT COUNT(*) AS n FROM "{table}";')
    return rows[0]["n"]


def describe_table(config: Config, table: str) -> list[dict]:
    """Return column definitions for a table."""
    if not table.replace("_", "").isalnum():
        raise ValueError(f"Invalid table name: {table}")

    return query(
        config,
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
        ORDER BY ordinal_position;
        """,
        (table,),
    )
