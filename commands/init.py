"""
dbsync init

Interactive setup. Prompts for connection details,
tests them, and writes ~/.dbsync.json.
"""

import getpass
import sys

import db
from config import Config, save, CONFIG_PATH


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def _ask(prompt: str, default: str = "") -> str:
    """Prompt for a value with an optional default."""
    if default:
        raw = input(f"  {prompt} [{default}]: ").strip()
        return raw or default
    return input(f"  {prompt}: ").strip()


def run() -> int:
    print()
    print(f"{BOLD}dbsync init{RESET}")
    print(f"{DIM}Setting up {CONFIG_PATH}{RESET}")
    print()

    print("Aiven connection details")
    print(f"{DIM}(from console.aiven.io → pg-5400 → Overview){RESET}")
    print()

    host = _ask("Host")
    port = _ask("Port", "28480")
    database = _ask("Database", "defaultdb")
    user = _ask("User", "avnadmin")

    print()
    print("Password")
    print(f"{DIM}(input is hidden){RESET}")
    password = getpass.getpass("  Password: ")

    print()
    print("IEMS project path")
    print(f"{DIM}(used by 'dbsync upgrade' to run migrations){RESET}")
    iems_path = _ask("Absolute path to IEMS folder")

    print()
    print("Aiven CA certificate")
    print(f"{DIM}(from console.aiven.io → pg-5400 → Overview → CA certificate){RESET}")
    sslrootcert = _ask(
        "Path to CA certificate",
        str(__import__("pathlib").Path.home() / "aiven-ca.pem"),
    )

    config = Config(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password,
        sslmode="verify-ca",
        sslrootcert=sslrootcert,
        iems_path=iems_path,
    )

    # -----------------------------------------------------
    # TEST CONNECTION
    # -----------------------------------------------------

    print()
    print(f"{DIM}[ … ] Testing connection…{RESET}", end="\r")

    ok, ms, detail = db.test_connection(config)

    if not ok:
        print(f"{RED}[ ✗ ] Connection failed: {detail}{RESET}          ")
        print()
        print("Config NOT saved. Fix the details and try again.")
        return 1

    print(f"{GREEN}[ ✓ ]{RESET} Connected in {ms}ms                    ")

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    save(config)

    print(f"{GREEN}[ ✓ ]{RESET} Config saved to {CONFIG_PATH}")
    print()
    print(f"Run {BOLD}python dbsync.py status{RESET} to see the schema.")
    print()

    return 0