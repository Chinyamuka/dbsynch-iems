"""
dbsync database helpers.

Wraps psycopg2 with:

  connect(config)          - open a connection to Aiven
  connect_local(config)    - open a connection to local Postgres
  test_connection(config)  - ping Aiven, return latency
  test_local_connection(config) - ping local, return latency
  query() / execute()      - run SQL, return rows
  get_alembic_version()    - read the current schema version
  list_tables()            - list tables in public schema
  count_rows()             - row count for a table
  describe_table()         - column definitions

Both targets speak the same Postgres protocol, so
query/execute/etc. work against either. The only
difference is which URI they use.
"""

import time
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from config import Config


# =========================================================
# CONNECTION — AIVEN
# =========================================================

@contextmanager
def connect(config: Config):
    """Open a connection to Aiven."""
    conn = psycopg2.connect(
        config.uri(),
        connect_timeout=config.timeout,
    )
    try:
        yield conn
    finally:
        conn.close()


def test_connection(config: Config) -> tuple[bool, int, str]:
    """Check whether Aiven is reachable."""
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
# CONNECTION — LOCAL
# =========================================================

@contextmanager
def connect_local(config: Config):
    """Open a connection to the local Postgres database."""
    if not config.local_uri:
        raise RuntimeError(
            "No local_uri set. Run: python dbsync.py config set-local <URI>"
        )
    conn = psycopg2.connect(
        config.local_uri,
        connect_timeout=config.timeout,
    )
    try:
        yield conn
    finally:
        conn.close()


def test_local_connection(config: Config) -> tuple[bool, int, str]:
    """Check whether the local database is reachable."""
    t0 = time.perf_counter()
    try:
        if not config.local_uri:
            return False, 0, "No local_uri configured"

        conn = psycopg2.connect(
            config.local_uri,
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
# QUERIES (target-agnostic — pass a URI or a config)
# =========================================================
#
# These take a raw connection URI so callers can use
# them against either Aiven or local. Aiven-specific
# helpers (list_tables etc.) still accept Config and
# resolve to config.uri(); local callers can either
# wrap or call the raw *_uri variants.

def query_uri(uri: str, sql: str, params: tuple = (), timeout: int = 30) -> list[dict]:
    """Run a SELECT against any Postgres URI, return rows as dicts."""
    conn = psycopg2.connect(uri, connect_timeout=timeout)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def execute_uri(uri: str, sql: str, params: tuple = (), timeout: int = 30) -> int:
    """Run a non-SELECT against any Postgres URI, return affected row count."""
    conn = psycopg2.connect(uri, connect_timeout=timeout)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
    finally:
        conn.close()


# =========================================================
# QUERIES — AIVEN (existing API, unchanged)
# =========================================================

def query(config: Config, sql: str, params: tuple = ()) -> list[dict]:
    """Run a SELECT against Aiven."""
    return query_uri(config.uri(), sql, params, timeout=config.timeout)


def execute(config: Config, sql: str, params: tuple = ()) -> int:
    """Run a non-SELECT against Aiven."""
    return execute_uri(config.uri(), sql, params, timeout=config.timeout)


# =========================================================
# SCHEMA INSPECTION — AIVEN (existing)
# =========================================================

def get_alembic_version(config: Config) -> str | None:
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
    if not table.replace("_", "").isalnum():
        raise ValueError(f"Invalid table name: {table}")
    rows = query(config, f'SELECT COUNT(*) AS n FROM "{table}";')
    return rows[0]["n"]


def describe_table(config: Config, table: str) -> list[dict]:
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
