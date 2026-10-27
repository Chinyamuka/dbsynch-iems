"""
Shared helpers for entity CRUD.

Every prompt validates at the terminal so the operator
sees the problem immediately, not after a DB exception.

Consistent style:

    field_name:  <prompt>       (required)
    field_name [value]:         (with default)
    field_name (optional):      (optional)
"""

import getpass
import sys

import db


GREEN = "\033[32m"
RED   = "\033[31m"
YELLOW = "\033[33m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


# =========================================================
# PROMPTS
# =========================================================

def ask(prompt: str, default: str = "") -> str:
    """Prompt for a required or defaulted value."""
    if default:
        raw = input(f"  {prompt} [{default}]: ").strip()
        return raw or default
    return input(f"  {prompt}: ").strip()


def ask_optional(prompt: str) -> str:
    """Prompt for an optional value. Empty means empty."""
    return input(f"  {prompt} (optional): ").strip()


def ask_password(prompt: str = "Password") -> str:
    """Prompt for a password (hidden input)."""
    return getpass.getpass(f"  {prompt}: ")


def ask_confirm(prompt: str, require_word: str = "") -> bool:
    """
    Ask for confirmation.

    If require_word is non-empty, the user must type that
    exact word (case-insensitive) to proceed. Otherwise
    'y' or 'yes' works.
    """
    if require_word:
        raw = input(f"  {prompt} Type '{require_word}' to confirm: ").strip().lower()
        return raw == require_word.lower()
    raw = input(f"  {prompt} [y/N]: ").strip().lower()
    return raw in ("y", "yes")


# =========================================================
# DB HELPERS (target-agnostic — pass local_uri)
# =========================================================

def local_query(config, sql: str, params: tuple = ()) -> list[dict]:
    """Query against the local database."""
    return db.query_uri(config.local_uri, sql, params, timeout=config.timeout)


def local_execute(config, sql: str, params: tuple = ()) -> int:
    """Execute against the local database."""
    return db.execute_uri(config.local_uri, sql, params, timeout=config.timeout)


# =========================================================
# OUTPUT HELPERS
# =========================================================

def print_table(headers: list[str], rows: list[list]) -> None:
    """Print a simple aligned table."""
    if not rows:
        print(f"  {DIM}(no rows){RESET}")
        return

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell) if cell is not None else ""))

    header_line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(f"  {BOLD}{header_line}{RESET}")
    print(f"  {'-' * len(header_line)}")
    for row in rows:
        cells = [str(c) if c is not None else "NULL" for c in row]
        print("  " + "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells)))


def pause() -> None:
    """Wait for the user to press Enter."""
    input(f"\n  {DIM}Press Enter to continue…{RESET}")


# =========================================================
# SAFETY
# =========================================================

def ensure_local_configured(config) -> bool:
    """Fail with a helpful message if local_uri is not set."""
    if not config.local_uri:
        print(f"{RED}[ ✗ ] local_uri not set.{RESET}")
        print()
        print("Run:")
        print(f"  {BOLD}python dbsync.py config set-local "
              f"postgresql://user:pass@localhost:5432/iems{RESET}")
        return False
    return True
