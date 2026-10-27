"""
dbsync admin

Interactive menu for CRUD against the local Postgres
database.

Phase 1: Departments
Phase 2: + Categories, Locations
Phase 3+: Equipment, Users
"""

import db
from commands.entities import base
from commands.entities import department as ent_department
from commands.entities import category as ent_category
from commands.entities import location as ent_location


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


ENTITIES = [
    ("1", "Departments", ent_department),
    ("2", "Categories", ent_category),
    ("3", "Locations", ent_location),
]


def _entity_menu(config, name: str, module) -> None:
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


def run(config, args) -> int:
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
