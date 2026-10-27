"""
Category CRUD for dbsync admin.

Categories are simpler than Department — just name
(unique) and description. Same structure, different
table.
"""

from commands.entities import base


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def list_all(config) -> None:
    print()
    print(f"{BOLD}Categories{RESET}")
    print()

    rows = base.local_query(
        config,
        'SELECT id, name, description FROM category ORDER BY name',
    )

    if not rows:
        print(f"  {DIM}No categories yet.{RESET}")
        print()
        print(f"  Use option {BOLD}2{RESET} to create one.")
        return

    base.print_table(
        ["ID", "Name", "Description"],
        [[r["id"], r["name"], r["description"] or ""] for r in rows],
    )

    print(f"\n  {DIM}{len(rows)} categories{RESET}")


def create(config):
    print()
    print(f"{BOLD}Create category{RESET}")
    print()

    name = base.ask("Name")
    if not name:
        print(f"{RED}[ ✗ ] Name is required.{RESET}")
        return None

    existing = base.local_query(
        config,
        'SELECT id FROM category WHERE lower(name) = lower(%s)',
        (name,),
    )
    if existing:
        print(f"{RED}[ ✗ ] A category named '{name}' already exists "
              f"(id={existing[0]['id']}).{RESET}")
        return None

    description = base.ask_optional("Description")

    # Confirmation
    print()
    print(f"  About to create category {BOLD}{name}{RESET}")
    if not base.ask_confirm("Create?"):
        print("  Aborted.")
        return None

    try:
        base.local_execute(
            config,
            'INSERT INTO category (name, description) VALUES (%s, %s)',
            (name, description or None),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Insert failed: {e}{RESET}")
        return None

    row = base.local_query(
        config,
        'SELECT id FROM category WHERE lower(name) = lower(%s)',
        (name,),
    )
    new_id = row[0]["id"] if row else None

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Category '{name}' created (id={new_id})")
    return new_id


def edit(config):
    print()
    print(f"{BOLD}Edit category{RESET}")
    print()

    cat_id = base.ask("Category ID")
    if not cat_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        'SELECT id, name, description FROM category WHERE id = %s',
        (int(cat_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No category with id={cat_id}.{RESET}")
        return False

    c = row[0]
    print()
    print(f"  Current name: {c['name']}")
    print(f"  Current description: {c['description'] or '(empty)'}")
    print()

    new_name = base.ask("Name", default=c["name"]).strip()
    if not new_name:
        print(f"{RED}[ ✗ ] Name cannot be empty.{RESET}")
        return False

    if new_name.lower() != c["name"].lower():
        clash = base.local_query(
            config,
            'SELECT id FROM category WHERE lower(name) = lower(%s) AND id != %s',
            (new_name, int(cat_id)),
        )
        if clash:
            print(f"{RED}[ ✗ ] Another category is already named '{new_name}'.{RESET}")
            return False

    new_desc = base.ask("Description", default=c["description"] or "").strip()

    try:
        base.local_execute(
            config,
            'UPDATE category SET name = %s, description = %s WHERE id = %s',
            (new_name, new_desc or None, int(cat_id)),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Update failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Category id={cat_id} updated")
    return True


def delete(config):
    print()
    print(f"{BOLD}Delete category{RESET}")
    print()

    cat_id = base.ask("Category ID")
    if not cat_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        'SELECT id, name FROM category WHERE id = %s',
        (int(cat_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No category with id={cat_id}.{RESET}")
        return False

    # FK check — equipment.category_id
    equip_count = base.local_query(
        config,
        'SELECT COUNT(*) AS n FROM equipment WHERE category_id = %s',
        (int(cat_id),),
    )[0]["n"]

    if equip_count > 0:
        print(f"{RED}[ ✗ ] Cannot delete: {equip_count} equipment "
              f"item(s) use this category.{RESET}")
        return False

    print(f"  Name: {row[0]['name']}")
    print()

    if not base.ask_confirm(f"Delete category id={cat_id}?", require_word="delete"):
        print("  Aborted.")
        return False

    try:
        base.local_execute(
            config,
            'DELETE FROM category WHERE id = %s',
            (int(cat_id),),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Delete failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Category id={cat_id} deleted")
    return True
