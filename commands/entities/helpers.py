"""
Shared entity helpers for pickers and typed input.

Kept separate from base.py so that base.py stays
focused on prompts and DB access. These helpers are
used by entities that have foreign keys (Equipment)
or enum fields (Equipment status/condition).
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from commands.entities import base


GREEN = "\033[32m"
RED   = "\033[31m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"


def pick_from_list(prompt: str, items: list, label_fn=None):
    """
    Numbered menu. Returns the chosen item (dict or
    whatever's in the list) or None if the user cancels
    (empty input for optional, invalid repeatedly).

    items: list of dicts with at least 'id' and 'name'
           OR list of any values — if label_fn is given,
           it's used to render the label; otherwise str().
    """
    if not items:
        print(f"  {RED}No options available.{RESET}")
        return None

    print()
    for i, item in enumerate(items, start=1):
        if label_fn:
            label = label_fn(item)
        elif isinstance(item, dict):
            label = item.get("name", str(item))
        else:
            label = str(item)
        print(f"    {i}. {label}")
    print()

    raw = input(f"  {prompt} [1-{len(items)}, empty=cancel]: ").strip()
    if not raw:
        return None

    if not raw.isdigit():
        print(f"  {RED}Invalid choice.{RESET}")
        return None

    idx = int(raw)
    if idx < 1 or idx > len(items):
        print(f"  {RED}Choice out of range.{RESET}")
        return None

    return items[idx - 1]


def pick_enum(prompt: str, values: list, default: str = ""):
    """
    Numbered menu for a fixed list of strings.
    Returns the chosen string or None on cancel.
    """
    print()
    for i, v in enumerate(values, start=1):
        marker = " (current)" if v == default else ""
        print(f"    {i}. {v}{marker}")
    print()

    if default:
        raw = input(f"  {prompt} [1-{len(values)}, Enter=keep current]: ").strip()
        if not raw:
            return default
    else:
        raw = input(f"  {prompt} [1-{len(values)}]: ").strip()

    if not raw.isdigit():
        print(f"  {RED}Invalid choice.{RESET}")
        return None

    idx = int(raw)
    if idx < 1 or idx > len(values):
        print(f"  {RED}Choice out of range.{RESET}")
        return None

    return values[idx - 1]


def ask_date(prompt: str, default: str = "") -> str | None:
    """
    Prompt for a date in YYYY-MM-DD. Empty is allowed
    and returned as None. Returns a string in YYYY-MM-DD
    or None on cancel/invalid.
    """
    if default:
        raw = input(f"  {prompt} [{default}] (YYYY-MM-DD, empty to clear): ").strip()
        if not raw:
            return default
    else:
        raw = input(f"  {prompt} (YYYY-MM-DD, optional): ").strip()

    if not raw:
        return None

    try:
        datetime.strptime(raw, "%Y-%m-%d")
        return raw
    except ValueError:
        print(f"  {RED}Not a valid date. Expected YYYY-MM-DD.{RESET}")
        return None


def ask_decimal(prompt: str, default: str = "") -> str | None:
    """
    Prompt for a decimal number. Returns a string or
    None. Not converted to Decimal here — psycopg2 will
    handle it, but we validate format first.
    """
    if default:
        raw = input(f"  {prompt} [{default}] (empty to clear): ").strip()
        if not raw:
            return default
    else:
        raw = input(f"  {prompt} (optional): ").strip()

    if not raw:
        return None

    try:
        Decimal(raw)
        return raw
    except InvalidOperation:
        print(f"  {RED}Not a valid number.{RESET}")
        return None
