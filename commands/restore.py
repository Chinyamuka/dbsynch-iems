"""
dbsync restore <path> --yes

Load a .sql file into Aiven.

DESTRUCTIVE. Requires --yes to proceed. If the target
contains data, the restore may overwrite rows or fail
mid-file on duplicate keys.

Before running, do a dbsync dump so you have a recovery
point. If you skip that, restore warns but does not
block.
"""

import shutil
import subprocess
from pathlib import Path

from config import Config
import db


GREEN = "\033[32m"
RED   = "\033[31m"
YELLOW = "\033[33m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run(config: Config, args) -> int:

    print()
    print(f"{BOLD}dbsync restore{RESET}")
    print(f"  To:  {config.display_uri()}")

    # -----------------------------------------------------
    # INPUT FILE
    # -----------------------------------------------------

    if not getattr(args, "path", None):
        print(f"{RED}Usage: dbsync restore <path.sql> --yes{RESET}")
        return 1

    src = Path(args.path).expanduser().resolve()

    if not src.exists():
        print(f"{RED}[ ✗ ] File not found: {src}{RESET}")
        return 1

    if not src.is_file():
        print(f"{RED}[ ✗ ] Not a file: {src}{RESET}")
        return 1

    if src.stat().st_size == 0:
        print(f"{RED}[ ✗ ] File is empty: {src}{RESET}")
        return 1

    size = src.stat().st_size
    if size < 1024:
        size_str = f"{size}B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f}KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f}MB"

    print(f"  From: {src} ({size_str})")
    print()

    if shutil.which("psql") is None:
        print(f"{RED}[ ✗ ] psql is not installed or not on PATH.{RESET}")
        print()
        print("Install it with:")
        print("  Ubuntu/Debian: sudo apt install postgresql-client")
        print("  macOS:         brew install postgresql")
        print()
        return 1

    # -----------------------------------------------------
    # SAFETY CHECKS
    # -----------------------------------------------------

    ok, _, detail = db.test_connection(config)
    if not ok:
        print(f"{RED}[ ✗ ] Cannot reach Aiven: {detail}{RESET}")
        return 1

    try:
        tables = db.list_tables(config)
    except Exception as e:
        print(f"{RED}[ ✗ ] Could not list tables: {e}{RESET}")
        return 1

    has_data = False
    total_rows = 0
    for t in tables:
        try:
            n = db.count_rows(config, t)
            total_rows += n
            if n > 0:
                has_data = True
        except Exception:
            # A timeout here is not fatal — continue,
            # just note it.
            pass

    if has_data:
        print(f"{YELLOW}[ ! ]{RESET} Aiven currently has {len(tables)} tables, "
              f"~{total_rows} rows.")
        print(f"{YELLOW}[ ! ]{RESET} Restoring may overwrite or duplicate data.")
        print()

    # -----------------------------------------------------
    # CONFIRMATION
    # -----------------------------------------------------

    if not getattr(args, "yes", False):
        print(f"{RED}This operation will modify Aiven.{RESET}")
        print(f"Re-run with {BOLD}--yes{RESET} to confirm:")
        print(f"  python dbsync.py restore {src.name} --yes")
        print()
        print(f"{DIM}Recommended before running:{RESET}")
        print(f"{DIM}  python dbsync.py dump{RESET}")
        print()
        return 1

    # -----------------------------------------------------
    # RESTORE
    # -----------------------------------------------------

    print(f"{DIM}[ … ] Running psql -f …{RESET}")
    print()

    result = subprocess.run(
        [
            "psql",
            "--set", "ON_ERROR_STOP=1",  # abort on first error
            "-d", config.uri(),
            "-f", str(src),
        ],
        capture_output=True,
        text=True,
    )

    print()

    # psql prints progress to stdout even on success
    if result.stdout:
        # Show last 20 lines of stdout so user sees completion
        lines = result.stdout.rstrip().splitlines()
        for line in lines[-20:]:
            print(f"  {line}")
        print()

    if result.returncode != 0:
        print(f"{RED}[ ✗ ] psql failed (exit {result.returncode}).{RESET}")
        if result.stderr:
            print(result.stderr)
        print()
        print(f"{DIM}If the restore stopped mid-file, Aiven is in an")
        print(f"intermediate state. Restore from a previous dump")
        print(f"taken with `python dbsync.py dump`.{RESET}")
        print()
        return result.returncode

    print(f"{GREEN}[ ✓ ]{RESET} Restore completed successfully.")
    print()
    print(f"{DIM}  Verify with:{RESET}")
    print(f"{DIM}    python dbsync.py status{RESET}")
    print()
    return 0
