"""
dbsync admin

Interactive menu for CRUD against the local Postgres
database.

Phase 1: Departments only.
Phase 2+: Categories, Locations, Equipment, Users.
"""

import sys

import db
from commands.entities import base
from commands.entities import department as ent_department


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


# =========================================================
# MENU DEFINITIONS
# =========================================================
#
# Phase 1: only Departments. Other entities are listed
# but disabled (marked "coming soon") so the operator
# sees the roadmap without being able to reach a stub.

ENTITIES = [
    ("1", "Departments", ent_department),
    # ("2", "Categories", ent_category),      # Phase 2
    # ("3", "Locations",  ent_location),      # Phase 2
    # ("4", "Equipment",  ent_equipment),     # Phase 3
    # ("5", "Users",      ent_user),          # Phase 3
]


# =========================================================
# SUB-MENU FOR AN ENTITY
# =========================================================

def _entity_menu(config, name: str, module) -> None:
    """CRUD sub-menu for a single entity."""
    while True:
        print()
        print(f"{BOLD}{name}{RESET}")
        print(f"{DIM}{'-' * len(name)}{RESET}")
        print()
        print("  1. List")
        print("  2. Create")
        print("  3. Edit")
        print("  4. Delete")
        print("  b. Back")
        print()

        choice = input("  Choose [1-4, b]: ").strip().lower()

        if choice in ("b", "back", "q"):
            return
        elif choice == "1":
            module.list_all(config)
            base.pause()
        elif choice == "2":
            module.create(config)
            base.pause()
        elif choice == "3":
            module.edit(config)
            base.pause()
        elif choice == "4":
            module.delete(config)
            base.pause()
        else:
            print(f"  {RED}Unknown choice.{RESET}")


# =========================================================
# TOP MENU
# =========================================================

def run(config, args) -> int:
    # Pre-flight
    if not base.ensure_local_configured(config):
        return 1

    print()
    print(f"{DIM}[ … ] Testing local connection…{RESET}", end="\r")

    ok, ms, detail = db.test_local_connection(config)
    if not ok:
        print(f"{RED}[ ✗ ] Local DB unreachable: {detail}{RESET}          ")
        return 1

    print(f"{GREEN}[ ✓ ]{RESET} Connected in {ms}ms                    ")

    while True:
        print()
        print(f"{BOLD}dbsync admin{RESET}")
        print(f"{DIM}{'-' * 12}{RESET}")
        print(f"{DIM}Target: {config.display_local_uri()}{RESET}")
        print()
        print("  What do you want to manage?")
        print()
        for key, name, _module in ENTITIES:
            print(f"    {key}. {name}")
        print()
        print("    q. Quit")
        print()

        choice = input("  Choose: ").strip().lower()

        if choice in ("q", "quit", "exit"):
            print()
            print(f"{DIM}Goodbye.{RESET}")
            return 0

        # Look up
        hit = None
        for key, name, module in ENTITIES:
            if choice == key:
                hit = (name, module)
                break

        if hit:
            name, module = hit
            _entity_menu(config, name, module)
        else:
            print(f"  {RED}Unknown choice.{RESET}")
