"""
dbsync status

Prints:
- Whether Aiven is reachable and the latency
- The current schema version
- The number of tables
- A summary of key rows (users, equipment)
"""

from config import Config
import db


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run(config: Config) -> int:
    """Return 0 on success, non-zero on failure."""

    print()
    print(f"{BOLD}dbsync status{RESET}")
    print(f"{DIM}{config.display_uri()}{RESET}")
    print()

    # -----------------------------------------------------
    # CONNECTIVITY
    # -----------------------------------------------------

    print(f"{DIM}[ … ] Connecting to Aiven…{RESET}", end="\r")

    ok, ms, detail = db.test_connection(config)

    if not ok:
        print(f"{RED}[ ✗ ] Cannot reach Aiven: {detail}{RESET}          ")
        print()
        print("Check:")
        print("  - Is your internet connection up?")
        print("  - Is Aiven's service running? (console.aiven.io → pg-5400)")
        print("  - Is port 28480 blocked by your ISP?")
        print()
        return 1

    print(f"{GREEN}[ ✓ ]{RESET} Connected in {ms}ms                    ")

    # -----------------------------------------------------
    # SCHEMA VERSION
    # -----------------------------------------------------

    version = db.get_alembic_version(config)

    if version:
        print(f"{GREEN}[ ✓ ]{RESET} Schema version: {BOLD}{version}{RESET}")
    else:
        print(f"{RED}[ ! ]{RESET} No alembic_version row — schema not migrated")

    # -----------------------------------------------------
    # TABLES
    # -----------------------------------------------------

    tables = db.list_tables(config)

    print(f"{GREEN}[ ✓ ]{RESET} Tables: {len(tables)}")

    # -----------------------------------------------------
    # ROW COUNTS
    # -----------------------------------------------------

    if tables:
        print()
        print(f"{BOLD}Row counts{RESET}")
        print(f"{DIM}{'-' * 40}{RESET}")

        for name in tables:
            try:
                n = db.count_rows(config, name)
                print(f"  {name:30} {n:>8}")
            except Exception as e:
                print(f"  {name:30} {RED}error{RESET}  {e}")

    print()
    return 0
