"""
dbsync push

Apply pending Alembic migrations to Aiven.

Delegates to `flask db upgrade` inside the IEMS project
with DATABASE_URL pointing at Aiven. Does NOT copy data —
schema changes only.

Finds the `flask` binary in this order:
1. <iems_path>/venv/bin/flask  (the IEMS project's venv)
2. `flask` on PATH             (an active venv or system install)

Fails with a clear message if neither works.

Idempotent: running push when Aiven is already at head
prints "Aiven schema is now at <head>" and exits 0.
"""

import os
import shutil
import subprocess

from config import Config


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def _resolve_flask(iems_path: str) -> str:
    """
    Return the path to a usable `flask` executable.

    Prefers the IEMS project's own venv so the command
    works regardless of what the caller's shell has
    activated. Falls back to PATH. Raises with a clear
    message if neither is available.
    """
    # 1. IEMS venv
    candidate = os.path.join(iems_path, "venv", "bin", "flask")
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate

    # 2. PATH
    on_path = shutil.which("flask")
    if on_path:
        return on_path

    raise FileNotFoundError(
        "Could not find a `flask` executable.\n"
        f"  - Tried: {candidate}\n"
        f"  - Also tried: PATH lookup (not found)\n"
        f"Install Flask in the IEMS venv, or activate it before running dbsync push."
    )


def _run(flask_bin: str, argv: list[str], cwd: str, env: dict):
    """Run `flask <argv...>` and return (rc, stdout, stderr)."""
    result = subprocess.run(
        [flask_bin] + argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def run(config: Config, args) -> int:
    if not config.iems_path:
        print(
            f"{RED}No iems_path set in config.{RESET}\n"
            f"Run: python dbsync.py init"
        )
        return 1

    iems_path = config.iems_path

    if not os.path.isdir(iems_path):
        print(f"{RED}iems_path does not exist: {iems_path}{RESET}")
        return 1

    # Resolve flask up front — better to fail before
    # printing "Current Aiven version" than after.
    try:
        flask_bin = _resolve_flask(iems_path)
    except FileNotFoundError as e:
        print(f"{RED}[ ✗ ] {e}{RESET}")
        return 1

    env = os.environ.copy()
    env["DATABASE_URL"] = config.uri()

    print()
    print(f"{BOLD}dbsync push{RESET}")
    print(f"  Aiven: {config.display_uri()}")
    print(f"  IEMS:  {iems_path}")
    print(f"  flask: {flask_bin}")
    print()

    # -----------------------------------------------------
    # CURRENT VERSION
    # -----------------------------------------------------

    print(f"{DIM}[ … ] Reading current migration version…{RESET}", end="\r")

    rc, out, err = _run(flask_bin, ["db", "current"], cwd=iems_path, env=env)

    if rc != 0:
        print(f"{RED}[ ✗ ] flask db current failed.{RESET}")
        print(err or out)
        return rc

    lines = [ln for ln in (out or "").splitlines() if ln.strip()]
    version = lines[-1].strip() if lines else "(none)"
    print(f"{GREEN}[ ✓ ]{RESET} Current Aiven version: {BOLD}{version}{RESET}")
    print()

    # -----------------------------------------------------
    # CONFIRM
    # -----------------------------------------------------

    if not getattr(args, "yes", False):
        answer = input("Apply pending migrations to Aiven? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    # -----------------------------------------------------
    # UPGRADE
    # -----------------------------------------------------

    print()
    print(f"{DIM}[ … ] Running flask db upgrade…{RESET}")
    print()

    result = subprocess.run(
        [flask_bin, "db", "upgrade"],
        cwd=iems_path,
        env=env,
    )

    print()

    if result.returncode != 0:
        print(f"{RED}[ ✗ ] flask db upgrade failed (exit {result.returncode}).{RESET}")
        print()
        print("Nothing has been committed to Aiven if the failing")
        print("migration is transactional (Postgres DDL is). Check")
        print("the migration file and try again.")
        return result.returncode

    # -----------------------------------------------------
    # CONFIRM NEW VERSION
    # -----------------------------------------------------

    rc, out, _ = _run(flask_bin, ["db", "current"], cwd=iems_path, env=env)
    lines = [ln for ln in (out or "").splitlines() if ln.strip()]
    version_now = lines[-1].strip() if lines else "(unknown)"

    print(f"{GREEN}[ ✓ ]{RESET} Aiven schema is now at {BOLD}{version_now}{RESET}")
    print()
    return 0
