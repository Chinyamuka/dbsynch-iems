"""
dbsync sql "<query>"

Run an ad-hoc query. SELECT statements print a table;
other statements print the affected row count.
"""

from config import Config
import db


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run(config: Config, args) -> int:

    sql = args.query
    if not sql:
        print(f"{RED}Usage: dbsync sql \"SELECT ...\"{RESET}")
        return 1

    print()
    print(f"{BOLD}dbsync sql{RESET}")
    print()

    ok, ms, detail = db.test_connection(config)
    if not ok:
        print(f"{RED}[ ✗ ] Cannot reach Aiven: {detail}{RESET}")
        return 1

    first_word = sql.strip().split()[0].upper() if sql.strip() else ""
    is_select = first_word in ("SELECT", "WITH", "EXPLAIN", "SHOW")

    try:
        if is_select:
            rows = db.query(config, sql)
            _print_rows(rows)
        else:
            affected = db.execute(config, sql)
            print(f"{GREEN}[ ✓ ]{RESET} {affected} row(s) affected")
            print()

    except Exception as e:
        print(f"{RED}[ ✗ ] Query failed: {e}{RESET}")
        print()
        return 1

    return 0


def _print_rows(rows):
    if not rows:
        print(f"{DIM}  (no rows){RESET}")
        print()
        return

    columns = list(rows[0].keys())

    widths = {c: len(c) for c in columns}
    for row in rows:
        for c in columns:
            v = row[c]
            width = len(str(v)) if v is not None else 4
            widths[c] = min(max(widths[c], width), 40)

    header = "  ".join(
        str(c)[:widths[c]].ljust(widths[c]) for c in columns
    )
    print(f"  {BOLD}{header}{RESET}")
    print(f"  {'-' * len(header)}")

    for row in rows:
        cells = []
        for c in columns:
            v = row[c]
            if v is None:
                s = "NULL"
            else:
                s = str(v).replace("\n", " ")
                if len(s) > widths[c]:
                    s = s[: widths[c] - 3] + "..."
            cells.append(s.ljust(widths[c]))
        print("  " + "  ".join(cells))

    print()
    print(f"  {DIM}{len(rows)} row(s){RESET}")
    print()
