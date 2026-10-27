"""
dbsync config

Sub-commands:

    config set-local <URI>   Store the local Postgres URI.
    config show              Print both URIs (passwords redacted).

The URI is stored in ~/.dbsync.json alongside the Aiven
config. Existing fields are preserved.
"""

import sys

import config as cfg
import db


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def run_set_local(args) -> int:
    uri = (getattr(args, "uri", "") or "").strip()
    if not uri:
        print(f"{RED}Usage: dbsync config set-local <postgresql://...>{RESET}")
        return 1

    if not uri.startswith(("postgresql://", "postgres://")):
        print(f"{RED}[ ✗ ] Not a postgres URI: {uri[:40]}...{RESET}")
        print("Expected: postgresql://user:password@host:port/database")
        return 1

    try:
        config = cfg.load()
    except FileNotFoundError as e:
        print(f"{RED}{e}{RESET}")
        return 1

    # Test connection BEFORE saving
    print(f"{DIM}[ … ] Testing local connection…{RESET}", end="\r")

    saved_uri = config.local_uri
    config.local_uri = uri

    ok, ms, detail = db.test_local_connection(config)

    if not ok:
        print(f"{RED}[ ✗ ] Local DB unreachable: {detail}{RESET}")
        print("URI not saved. Fix the details and try again.")
        config.local_uri = saved_uri
        return 1

    print(f"{GREEN}[ ✓ ]{RESET} Connected in {ms}ms                    ")

    cfg.save(config)
    print(f"{GREEN}[ ✓ ]{RESET} Local URI saved to {cfg.CONFIG_PATH}")
    print()
    print(f"{DIM}  {config.display_local_uri()}{RESET}")
    print()
    print(f"Run {BOLD}python dbsync.py admin{RESET} to manage records.")
    print()
    return 0


def run_show(args) -> int:
    try:
        config = cfg.load()
    except FileNotFoundError as e:
        print(f"{RED}{e}{RESET}")
        return 1

    print()
    print(f"{BOLD}dbsync config{RESET}")
    print(f"{DIM}{cfg.CONFIG_PATH}{RESET}")
    print()

    print(f"  {BOLD}Aiven{RESET}")
    print(f"    URI:   {config.display_uri()}")
    print(f"    IEMS:  {config.iems_path or '(not set)'}")
    print()

    print(f"  {BOLD}Local{RESET}")
    print(f"    URI:   {config.display_local_uri()}")
    print()

    return 0
