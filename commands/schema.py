"""
dbsync schema <table>

Print column definitions for one table.
"""

from config import Config
import db


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run(config: Config, args) -> int:
    if not args.table:
        print(f"{RED}Usage: dbsync schema <table>{RESET}")
        return 1

    table = args.table

    print()
    print(f"{BOLD}dbsync schema {table}{RESET}")
    print()

    ok, ms, detail = db.test_connection(config)
    if not ok:
        print(f"{RED}[ ✗ ] Cannot reach Aiven: {detail}{RESET}")
        return 1

    tables = db.list_tables(config)
    if table not in tables:
        print(f"{RED}[ ✗ ] Table '{table}' does not exist.{RESET}")
        print()
        print("Available tables:")
        for t in tables:
            print(f"  {t}")
        print()
        return 1

    try:
        columns = db.describe_table(config, table)
    except Exception as e:
        print(f"{RED}[ ✗ ] {e}{RESET}")
        return 1

    print(
        f"  {BOLD}"
        f"{'Column':<28} {'Type':<24} {'Null':<6} {'Default'}"
        f"{RESET}"
    )
    print(f"{DIM}  {'-' * 80}{RESET}")

    for c in columns:
        name = c["column_name"]
        ctype = c["data_type"]
        nullable = "yes" if c["is_nullable"] == "YES" else "no"
        default = c["column_default"] or ""
        if len(default) > 30:
            default = default[:27] + "..."
        print(
            f"  {name:<28} {ctype:<24} {nullable:<6} {default}"
        )

    print()
    print(f"  {DIM}{len(columns)} columns{RESET}")
    print()

    return 0
