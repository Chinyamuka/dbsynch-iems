"""
Department CRUD for dbsync admin.

Departments have only name (unique, case-insensitive)
and description. Simple enough to establish the
pattern for other entities.
"""

from commands.entities import base
import db


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


# =========================================================
# LIST
# =========================================================

def list_all(config) -> None:
    print()
    print(f"{BOLD}Departments{RESET}")
    print()

    rows = base.local_query(
        config,
        'SELECT id, name, description FROM department ORDER BY name',
    )

    if not rows:
        print(f"  {DIM}No departments yet.{RESET}")
        return

    base.print_table(
        ["ID", "Name", "Description"],
        [[r["id"], r["name"], r["description"] or ""] for r in rows],
    )

    print(f"\n  {DIM}{len(rows)} departments{RESET}")


# =========================================================
# CREATE
# =========================================================

def create(config):
    print()
    print(f"{BOLD}Create department{RESET}")
    print()

    name = base.ask("Name")
    if not name:
        print(f"{RED}[ ✗ ] Name is required.{RESET}")
        return None

    # Uniqueness check — case-insensitive
    existing = base.local_query(
        config,
        'SELECT id FROM department WHERE lower(name) = lower(%s)',
        (name,),
    )
    if existing:
        print(f"{RED}[ ✗ ] A department named '{name}' already exists "
              f"(id={existing[0]['id']}).{RESET}")
        return None

    description = base.ask_optional("Description")

    # Confirmation — catches typos in the name before insert
    print()
    print(f"  About to create department {BOLD}{name}{RESET}")
    if not base.ask_confirm("Create?"):
        print("  Aborted.")
        return None

    try:
        base.local_execute(
            config,
            'INSERT INTO department (name, description) VALUES (%s, %s)',
            (name, description or None),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Insert failed: {e}{RESET}")
        return None

    # Fetch the new ID
    row = base.local_query(
        config,
        'SELECT id FROM department WHERE lower(name) = lower(%s)',
        (name,),
    )
    new_id = row[0]["id"] if row else None

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Department '{name}' created (id={new_id})")
    return new_id


# =========================================================
# EDIT
# =========================================================

def edit(config):
    print()
    print(f"{BOLD}Edit department{RESET}")
    print()

    dept_id = base.ask("Department ID")
    if not dept_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        'SELECT id, name, description FROM department WHERE id = %s',
        (int(dept_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No department with id={dept_id}.{RESET}")
        return False

    d = row[0]
    print()
    print(f"  Current name: {d['name']}")
    print(f"  Current description: {d['description'] or '(empty)'}")
    print()

    new_name = base.ask("Name", default=d["name"]).strip()
    if not new_name:
        print(f"{RED}[ ✗ ] Name cannot be empty.{RESET}")
        return False

    # Uniqueness if name changed
    if new_name.lower() != d["name"].lower():
        clash = base.local_query(
            config,
            'SELECT id FROM department WHERE lower(name) = lower(%s) AND id != %s',
            (new_name, int(dept_id)),
        )
        if clash:
            print(f"{RED}[ ✗ ] Another department is already named '{new_name}'.{RESET}")
            return False

    new_desc = base.ask("Description", default=d["description"] or "").strip()

    try:
        base.local_execute(
            config,
            'UPDATE department SET name = %s, description = %s WHERE id = %s',
            (new_name, new_desc or None, int(dept_id)),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Update failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Department id={dept_id} updated")
    return True


# =========================================================
# DELETE
# =========================================================

def delete(config):
    print()
    print(f"{BOLD}Delete department{RESET}")
    print()

    dept_id = base.ask("Department ID")
    if not dept_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        'SELECT id, name FROM department WHERE id = %s',
        (int(dept_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No department with id={dept_id}.{RESET}")
        return False

    # Reference check — users FK
    user_count = base.local_query(
        config,
        'SELECT COUNT(*) AS n FROM "user" WHERE department_id = %s',
        (int(dept_id),),
    )[0]["n"]

    if user_count > 0:
        print(f"{RED}[ ✗ ] Cannot delete: {user_count} user(s) "
              f"reference this department.{RESET}")
        print("  Reassign them first, or deactivate them.")
        return False

    print(f"  Name: {row[0]['name']}")
    print()

    if not base.ask_confirm(f"Delete department id={dept_id}?", require_word="delete"):
        print("  Aborted.")
        return False

    try:
        base.local_execute(
            config,
            'DELETE FROM department WHERE id = %s',
            (int(dept_id),),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Delete failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Department id={dept_id} deleted")
    return True
