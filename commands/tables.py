"""
dbsync tables

Table listing with column counts, row estimates, and disk sizes.
"""

from config import Config
import db


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run(config: Config) -> int:
    print()
    print(f"{BOLD}dbsync tables{RESET}")
    print()

    ok, ms, detail = db.test_connection(config)
    if not ok:
        print(f"{RED}[ ✗ ] Cannot reach Aiven: {detail}{RESET}")
        return 1

    rows = db.query(
        config,
        """
        SELECT
            c.relname                        AS name,
            GREATEST(c.reltuples, 0)::bigint AS row_estimate,
            pg_total_relation_size(c.oid)    AS size_bytes
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
        ORDER BY c.relname;
        """,
    )

    column_counts = {}
    for table_row in rows:
        name = table_row["name"]
        result = db.query(
            config,
            """
            SELECT COUNT(*) AS n
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s;
            """,
            (name,),
        )
        column_counts[name] = result[0]["n"]

    print(
        f"  {BOLD}"
        f"{'Table':<28} {'Columns':>8} {'Rows':>10} {'Size':>10}"
        f"{RESET}"
    )
    print(f"{DIM}  {'-' * 60}{RESET}")

    for r in rows:
        name = r["name"]
        n_cols = column_counts[name]
        n_rows = r["row_estimate"]
        size = _human_size(r["size_bytes"])
        print(
            f"  {name:<28} {n_cols:>8} {n_rows:>10,} {size:>10}"
        )

    print()
    print(f"  {DIM}{len(rows)} tables{RESET}")
    print()

    return 0


def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n / (1024 * 1024):.1f}MB"
