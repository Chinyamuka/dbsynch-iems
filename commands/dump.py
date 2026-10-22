"""
dbsync dump [path]

Dump the Aiven database to a .sql file.

Uses pg_dump (part of the PostgreSQL client tools).
Fails clearly if pg_dump is not on PATH.

Default output: <cwd>/iems-aiven-YYYYMMDD-HHMMSS.sql
Override with an explicit path argument.

Read-only against Aiven. No data is modified.
"""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from config import Config


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run(config: Config, args) -> int:

    print()
    print(f"{BOLD}dbsync dump{RESET}")
    print(f"  From: {config.display_uri()}")
    print()

    if shutil.which("pg_dump") is None:
        print(f"{RED}[ ✗ ] pg_dump is not installed or not on PATH.{RESET}")
        print()
        print("Install it with:")
        print("  Ubuntu/Debian: sudo apt install postgresql-client")
        print("  macOS:         brew install postgresql")
        print("  Windows:       install PostgreSQL, add bin/ to PATH")
        print()
        return 1

    if getattr(args, "path", None):
        out = Path(args.path).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        out = Path.cwd() / f"iems-aiven-{stamp}.sql"

    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"  To:   {out}")
    print()
    print(f"{DIM}[ … ] Running pg_dump…{RESET}")

    result = subprocess.run(
        [
            "pg_dump",
            "--no-owner",
            "--no-privileges",
            "--format=plain",
            "--file", str(out),
            config.uri(),
        ],
        capture_output=True,
        text=True,
    )

    print()

    if result.returncode != 0:
        print(f"{RED}[ ✗ ] pg_dump failed (exit {result.returncode}).{RESET}")
        if result.stderr:
            print(result.stderr)
        # Remove any partial file
        if out.exists():
            out.unlink()
        return result.returncode

    if not out.exists() or out.stat().st_size == 0:
        print(f"{RED}[ ✗ ] pg_dump reported success but the output file is empty.{RESET}")
        return 1

    size = out.stat().st_size
    if size < 1024:
        size_str = f"{size}B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f}KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f}MB"

    print(f"{GREEN}[ ✓ ]{RESET} Dumped {BOLD}{size_str}{RESET} to {out}")
    print()
    print(f"{DIM}  Restore with:{RESET}")
    print(f"{DIM}    python dbsync.py restore {out.name} --yes{RESET}")
    print()
    return 0
