"""
Location CRUD for dbsync admin.

Locations have name (unique), building, room, description.
The building and room fields are optional. All four are
managed together in edit.
"""

from commands.entities import base


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def list_all(config) -> None:
    print()
    print(f"{BOLD}Locations{RESET}")
    print()

    rows = base.local_query(
        config,
        'SELECT id, name, building, room FROM location ORDER BY name',
    )

    if not rows:
        print(f"  {DIM}No locations yet.{RESET}")
        print()
        print(f"  Use option {BOLD}2{RESET} to create one.")
        return

    base.print_table(
        ["ID", "Name", "Building", "Room"],
        [
            [
                r["id"],
                r["name"],
                r["building"] or "",
                r["room"] or "",
            ]
            for r in rows
        ],
    )

    print(f"\n  {DIM}{len(rows)} locations{RESET}")


def create(config):
    print()
    print(f"{BOLD}Create location{RESET}")
    print()

    name = base.ask("Name")
    if not name:
        print(f"{RED}[ ✗ ] Name is required.{RESET}")
        return None

    existing = base.local_query(
        config,
        'SELECT id FROM location WHERE lower(name) = lower(%s)',
        (name,),
    )
    if existing:
        print(f"{RED}[ ✗ ] A location named '{name}' already exists "
              f"(id={existing[0]['id']}).{RESET}")
        return None

    building = base.ask_optional("Building")
    room = base.ask_optional("Room")
    description = base.ask_optional("Description")

    print()
    print(f"  About to create location {BOLD}{name}{RESET}")
    if not base.ask_confirm("Create?"):
        print("  Aborted.")
        return None

    try:
        base.local_execute(
            config,
            'INSERT INTO location (name, building, room, description) '
            'VALUES (%s, %s, %s, %s)',
            (name, building or None, room or None, description or None),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Insert failed: {e}{RESET}")
        return None

    row = base.local_query(
        config,
        'SELECT id FROM location WHERE lower(name) = lower(%s)',
        (name,),
    )
    new_id = row[0]["id"] if row else None

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Location '{name}' created (id={new_id})")
    return new_id


def edit(config):
    print()
    print(f"{BOLD}Edit location{RESET}")
    print()

    loc_id = base.ask("Location ID")
    if not loc_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        'SELECT id, name, building, room, description '
        'FROM location WHERE id = %s',
        (int(loc_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No location with id={loc_id}.{RESET}")
        return False

    loc = row[0]
    print()
    print(f"  Current name: {loc['name']}")
    print(f"  Current building: {loc['building'] or '(empty)'}")
    print(f"  Current room: {loc['room'] or '(empty)'}")
    print(f"  Current description: {loc['description'] or '(empty)'}")
    print()

    new_name = base.ask("Name", default=loc["name"]).strip()
    if not new_name:
        print(f"{RED}[ ✗ ] Name cannot be empty.{RESET}")
        return False

    if new_name.lower() != loc["name"].lower():
        clash = base.local_query(
            config,
            'SELECT id FROM location WHERE lower(name) = lower(%s) AND id != %s',
            (new_name, int(loc_id)),
        )
        if clash:
            print(f"{RED}[ ✗ ] Another location is already named '{new_name}'.{RESET}")
            return False

    new_building = base.ask(
        "Building", default=loc["building"] or ""
    ).strip()
    new_room = base.ask(
        "Room", default=loc["room"] or ""
    ).strip()
    new_desc = base.ask(
        "Description", default=loc["description"] or ""
    ).strip()

    try:
        base.local_execute(
            config,
            'UPDATE location SET name = %s, building = %s, '
            'room = %s, description = %s WHERE id = %s',
            (new_name, new_building or None, new_room or None,
             new_desc or None, int(loc_id)),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Update failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Location id={loc_id} updated")
    return True


def delete(config):
    print()
    print(f"{BOLD}Delete location{RESET}")
    print()

    loc_id = base.ask("Location ID")
    if not loc_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        'SELECT id, name FROM location WHERE id = %s',
        (int(loc_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No location with id={loc_id}.{RESET}")
        return False

    equip_count = base.local_query(
        config,
        'SELECT COUNT(*) AS n FROM equipment WHERE location_id = %s',
        (int(loc_id),),
    )[0]["n"]

    if equip_count > 0:
        print(f"{RED}[ ✗ ] Cannot delete: {equip_count} equipment "
              f"item(s) reference this location.{RESET}")
        return False

    print(f"  Name: {row[0]['name']}")
    print()

    if not base.ask_confirm(f"Delete location id={loc_id}?", require_word="delete"):
        print("  Aborted.")
        return False

    try:
        base.local_execute(
            config,
            'DELETE FROM location WHERE id = %s',
            (int(loc_id),),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Delete failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Location id={loc_id} deleted")
    return True
