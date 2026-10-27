"""
Entity handlers for the dbsync admin menu.

Each entity lives in its own module and exports
four functions:

    list_all(config)      -> prints a table of rows
    create(config)        -> interactive create, returns new id or None
    edit(config)          -> interactive edit, returns True/False
    delete(config)        -> interactive delete, returns True/False

The dispatch table below maps menu keys to modules.
Adding a new entity is: create the module, add it
to this dict, add a menu entry in commands/admin.py.
"""

ENTITY_MODULES = {}


def register(key: str, module) -> None:
    ENTITY_MODULES[key] = module


def get(key: str):
    return ENTITY_MODULES.get(key)
