"""
Equipment CRUD for dbsync admin.

Equipment has:
- Unique asset_tag and serial_number
- Two foreign keys: category (required), location (optional)
- Two enums: status, condition
- Two dates: purchase_date, warranty_expiry
- One decimal: purchase_price
- One optional path: image_filename

The create/edit flows use FK pickers and enum menus,
not free-text IDs.
"""

from commands.entities import base
from commands.entities import helpers


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


# =========================================================
# ENUM VALUES — must match IEMS models exactly (case-sensitive)
# =========================================================

STATUSES = [
    "In Stock",
    "Assigned",
    "Under Maintenance",
    "Lost",
    "Retired",
    "Disposed",
]

CONDITIONS = [
    "Excellent",
    "Good",
    "Fair",
    "Poor",
    "Damaged",
]


# =========================================================
# FK LOOKUPS
# =========================================================

def _load_categories(config) -> list[dict]:
    return base.local_query(
        config,
        "SELECT id, name FROM category ORDER BY name",
    )


def _load_locations(config) -> list[dict]:
    return base.local_query(
        config,
        "SELECT id, name FROM location ORDER BY name",
    )


def _category_name(config, category_id) -> str:
    if category_id is None:
        return "(none)"
    rows = base.local_query(
        config,
        "SELECT name FROM category WHERE id = %s",
        (int(category_id),),
    )
    return rows[0]["name"] if rows else f"(deleted id={category_id})"


def _location_name(config, location_id) -> str:
    if location_id is None:
        return "(none)"
    rows = base.local_query(
        config,
        "SELECT name FROM location WHERE id = %s",
        (int(location_id),),
    )
    return rows[0]["name"] if rows else f"(deleted id={location_id})"


# =========================================================
# LIST
# =========================================================

def list_all(config) -> None:
    print()
    print(f"{BOLD}Equipment{RESET}")
    print()

    rows = base.local_query(
        config,
        """
        SELECT
            e.id,
            e.asset_tag,
            e.manufacturer,
            e.model,
            e.status,
            c.name AS category_name
        FROM equipment e
        LEFT JOIN category c ON c.id = e.category_id
        ORDER BY e.asset_tag
        """,
    )

    if not rows:
        print(f"  {DIM}No equipment yet.{RESET}")
        print()
        print(f"  Use option {BOLD}2{RESET} to create one.")
        return

    base.print_table(
        ["ID", "Asset Tag", "Manufacturer", "Model", "Category", "Status"],
        [
            [
                r["id"],
                r["asset_tag"],
                r["manufacturer"],
                r["model"],
                r["category_name"] or "",
                r["status"],
            ]
            for r in rows
        ],
    )

    print(f"\n  {DIM}{len(rows)} equipment records{RESET}")


# =========================================================
# CREATE
# =========================================================

def create(config):
    print()
    print(f"{BOLD}Create equipment{RESET}")
    print()

    # ---- Required fields ----
    asset_tag = base.ask("Asset Tag")
    if not asset_tag:
        print(f"{RED}[ ✗ ] Asset tag is required.{RESET}")
        return None

    # Uniqueness on asset_tag
    existing = base.local_query(
        config,
        "SELECT id FROM equipment WHERE lower(asset_tag) = lower(%s)",
        (asset_tag,),
    )
    if existing:
        print(f"{RED}[ ✗ ] Asset tag '{asset_tag}' already exists "
              f"(id={existing[0]['id']}).{RESET}")
        return None

    serial_number = base.ask_optional("Serial Number")
    if serial_number:
        existing = base.local_query(
            config,
            "SELECT id FROM equipment WHERE lower(serial_number) = lower(%s)",
            (serial_number,),
        )
        if existing:
            print(f"{RED}[ ✗ ] Serial number '{serial_number}' already exists "
                  f"(id={existing[0]['id']}).{RESET}")
            return None

    manufacturer = base.ask("Manufacturer")
    if not manufacturer:
        print(f"{RED}[ ✗ ] Manufacturer is required.{RESET}")
        return None

    model = base.ask("Model")
    if not model:
        print(f"{RED}[ ✗ ] Model is required.{RESET}")
        return None

    description = base.ask_optional("Description")

    # ---- Category (required FK) ----
    cats = _load_categories(config)
    if not cats:
        print(f"{RED}[ ✗ ] No categories exist. Create one first "
              f"(admin → Categories → Create).{RESET}")
        return None

    print(f"\n  {BOLD}Category{RESET}")
    cat = helpers.pick_from_list("Category", cats)
    if not cat:
        print("  Aborted.")
        return None
    category_id = cat["id"]

    # ---- Location (optional FK) ----
    locs = _load_locations(config)
    location_id = None
    if locs:
        print(f"\n  {BOLD}Location{RESET} (optional)")
        loc = helpers.pick_from_list("Location", locs)
        location_id = loc["id"] if loc else None
    else:
        print(f"\n  {DIM}No locations exist — skipping location.{RESET}")

    # ---- Status (enum, required) ----
    print(f"\n  {BOLD}Status{RESET}")
    status = helpers.pick_enum("Status", STATUSES)
    if not status:
        print("  Aborted.")
        return None

    # ---- Condition (enum, required) ----
    print(f"\n  {BOLD}Condition{RESET}")
    condition = helpers.pick_enum("Condition", CONDITIONS)
    if not condition:
        print("  Aborted.")
        return None

    # ---- Purchase info (optional) ----
    print(f"\n  {BOLD}Purchase information{RESET} (optional)")
    purchase_date = helpers.ask_date("Purchase date")
    purchase_price = helpers.ask_decimal("Purchase price")
    warranty_expiry = helpers.ask_date("Warranty expiry")

    # ---- Confirmation ----
    print()
    print(f"  About to create equipment:")
    print(f"    Asset tag:     {asset_tag}")
    print(f"    Manufacturer:  {manufacturer}")
    print(f"    Model:         {model}")
    print(f"    Category:      {cat['name']}")
    print(f"    Location:      {loc['name'] if location_id else '(none)'}")
    print(f"    Status:        {status}")
    print(f"    Condition:     {condition}")
    print()
    if not base.ask_confirm("Create?"):
        print("  Aborted.")
        return None

    # ---- Insert ----
    try:
        base.local_execute(
            config,
            """
            INSERT INTO equipment
                (asset_tag, serial_number, manufacturer, model,
                 description, category_id, location_id,
                 status, condition,
                 purchase_date, purchase_price, warranty_expiry,
                 updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                asset_tag,
                serial_number or None,
                manufacturer,
                model,
                description or None,
                int(category_id),
                int(location_id) if location_id else None,
                status,
                condition,
                purchase_date,
                purchase_price,
                warranty_expiry,
            ),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Insert failed: {e}{RESET}")
        return None

    row = base.local_query(
        config,
        "SELECT id FROM equipment WHERE lower(asset_tag) = lower(%s)",
        (asset_tag,),
    )
    new_id = row[0]["id"] if row else None

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Equipment '{asset_tag}' created (id={new_id})")
    return new_id


# =========================================================
# EDIT
# =========================================================

def edit(config):
    print()
    print(f"{BOLD}Edit equipment{RESET}")
    print()

    equip_id = base.ask("Equipment ID")
    if not equip_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        """
        SELECT
            id, asset_tag, serial_number, manufacturer, model,
            description, category_id, location_id,
            status, condition,
            purchase_date, purchase_price, warranty_expiry
        FROM equipment WHERE id = %s
        """,
        (int(equip_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No equipment with id={equip_id}.{RESET}")
        return False

    e = row[0]
    print()
    print(f"  Current: {e['asset_tag']} — {e['manufacturer']} {e['model']}")
    print()

    # ---- Text fields ----
    new_asset_tag = base.ask("Asset Tag", default=e["asset_tag"]).strip()
    if not new_asset_tag:
        print(f"{RED}[ ✗ ] Asset tag cannot be empty.{RESET}")
        return False

    if new_asset_tag.lower() != e["asset_tag"].lower():
        clash = base.local_query(
            config,
            "SELECT id FROM equipment WHERE lower(asset_tag) = lower(%s) AND id != %s",
            (new_asset_tag, int(equip_id)),
        )
        if clash:
            print(f"{RED}[ ✗ ] Asset tag '{new_asset_tag}' already used "
                  f"(id={clash[0]['id']}).{RESET}")
            return False

    new_serial = base.ask("Serial Number", default=e["serial_number"] or "").strip()
    if new_serial and new_serial.lower() != (e["serial_number"] or "").lower():
        clash = base.local_query(
            config,
            "SELECT id FROM equipment WHERE lower(serial_number) = lower(%s) AND id != %s",
            (new_serial, int(equip_id)),
        )
        if clash:
            print(f"{RED}[ ✗ ] Serial '{new_serial}' already used "
                  f"(id={clash[0]['id']}).{RESET}")
            return False

    new_manufacturer = base.ask("Manufacturer", default=e["manufacturer"]).strip()
    new_model = base.ask("Model", default=e["model"]).strip()
    new_description = base.ask("Description", default=e["description"] or "").strip()

    # ---- Category (FK) ----
    cats = _load_categories(config)
    if cats:
        print(f"\n  {BOLD}Category{RESET}")
        cat = helpers.pick_from_list("Category", cats)
        if not cat:
            print("  Aborted.")
            return False
        new_category_id = cat["id"]
    else:
        new_category_id = e["category_id"]

    # ---- Location (FK) ----
    locs = _load_locations(config)
    if locs:
        print(f"\n  {BOLD}Location{RESET} (optional, empty keeps current)")
        loc = helpers.pick_from_list("Location", locs)
        new_location_id = loc["id"] if loc else e["location_id"]
    else:
        new_location_id = e["location_id"]

    # ---- Status ----
    print(f"\n  {BOLD}Status{RESET}")
    new_status = helpers.pick_enum("Status", STATUSES, default=e["status"])
    if new_status is None:
        print("  Aborted.")
        return False

    # ---- Condition ----
    print(f"\n  {BOLD}Condition{RESET}")
    new_condition = helpers.pick_enum("Condition", CONDITIONS, default=e["condition"])
    if new_condition is None:
        print("  Aborted.")
        return False

    # ---- Purchase info ----
    print(f"\n  {BOLD}Purchase information{RESET}")
    new_purchase_date = helpers.ask_date(
        "Purchase date",
        default=e["purchase_date"].isoformat() if e["purchase_date"] else "",
    )
    new_purchase_price = helpers.ask_decimal(
        "Purchase price",
        default=str(e["purchase_price"]) if e["purchase_price"] else "",
    )
    new_warranty = helpers.ask_date(
        "Warranty expiry",
        default=e["warranty_expiry"].isoformat() if e["warranty_expiry"] else "",
    )

    # ---- Update ----
    try:
        base.local_execute(
            config,
            """
            UPDATE equipment SET
                asset_tag = %s,
                serial_number = %s,
                manufacturer = %s,
                model = %s,
                description = %s,
                category_id = %s,
                location_id = %s,
                status = %s,
                condition = %s,
                purchase_date = %s,
                purchase_price = %s,
                warranty_expiry = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (
                new_asset_tag,
                new_serial or None,
                new_manufacturer,
                new_model,
                new_description or None,
                int(new_category_id),
                int(new_location_id) if new_location_id else None,
                new_status,
                new_condition,
                new_purchase_date,
                new_purchase_price,
                new_warranty,
                int(equip_id),
            ),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Update failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Equipment id={equip_id} updated")
    return True


# =========================================================
# DELETE
# =========================================================

def delete(config):
    print()
    print(f"{BOLD}Delete equipment{RESET}")
    print()

    equip_id = base.ask("Equipment ID")
    if not equip_id.isdigit():
        print(f"{RED}[ ✗ ] Invalid ID.{RESET}")
        return False

    row = base.local_query(
        config,
        "SELECT id, asset_tag FROM equipment WHERE id = %s",
        (int(equip_id),),
    )
    if not row:
        print(f"{RED}[ ✗ ] No equipment with id={equip_id}.{RESET}")
        return False

    # FK check — equipment_assignment
    assign_count = base.local_query(
        config,
        "SELECT COUNT(*) AS n FROM equipment_assignment WHERE equipment_id = %s",
        (int(equip_id),),
    )[0]["n"]

    if assign_count > 0:
        print(f"{RED}[ ✗ ] Cannot delete: {assign_count} assignment(s) "
              f"reference this equipment.{RESET}")
        print("  Return the equipment first, or leave the history intact.")
        return False

    print(f"  Asset tag: {row[0]['asset_tag']}")
    print()

    if not base.ask_confirm(
        f"Delete equipment id={equip_id}?", require_word="delete"
    ):
        print("  Aborted.")
        return False

    try:
        base.local_execute(
            config,
            "DELETE FROM equipment WHERE id = %s",
            (int(equip_id),),
        )
    except Exception as e:
        print(f"{RED}[ ✗ ] Delete failed: {e}{RESET}")
        return False

    print()
    print(f"{GREEN}[ ✓ ]{RESET} Equipment id={equip_id} deleted")
    return True
