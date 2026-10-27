#!/usr/bin/env python3
"""
dbsync — local database manager for IEMS on Aiven.

Usage:
    dbsync init             First-run setup
    dbsync status           Connection, schema version, row counts
    dbsync tables           Table listing with column + row counts
    dbsync schema <table>   Column definitions for a table
    dbsync sql "<query>"    Run an ad-hoc query

Run 'dbsync <command> --help' for details.
"""

import argparse
import sys

import config as cfg
from commands import init as cmd_init
from commands import status as cmd_status
from commands import tables as cmd_tables
from commands import schema as cmd_schema
from commands import sql as cmd_sql
from commands import push as cmd_push
from commands import dump as cmd_dump
from commands import restore as cmd_restore
from commands import config as cmd_config
from commands import admin as cmd_admin


BOLD  = "\033[1m"
RED   = "\033[31m"
RESET = "\033[0m"


# =========================================================
# COMMAND WRAPPERS
# =========================================================

def _load_config():
    try:
        return cfg.load()
    except FileNotFoundError as e:
        print(f"{RED}{e}{RESET}", file=sys.stderr)
        return None


def cmd_init_wrapper(args) -> int:
    return cmd_init.run()


def cmd_status_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_status.run(config)


def cmd_tables_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_tables.run(config)


def cmd_schema_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_schema.run(config, args)


def cmd_sql_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_sql.run(config, args)


def cmd_push_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_push.run(config, args)


def cmd_dump_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_dump.run(config, args)


def cmd_restore_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_restore.run(config, args)


def cmd_config_wrapper(args) -> int:
    if args.config_command == "set-local":
        return cmd_config.run_set_local(args)
    if args.config_command == "show":
        return cmd_config.run_show(args)
    print(f"Unknown config subcommand: {args.config_command}")
    return 1


def cmd_admin_wrapper(args) -> int:
    config = _load_config()
    if config is None:
        return 1
    return cmd_admin.run(config, args)


# =========================================================
# ARGPARSE
# =========================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dbsync",
        description=(
            "Local database manager for IEMS on Aiven. "
            "Reuses the IEMS models and migration files."
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        metavar="<command>",
    )

    sub.add_parser(
        "init",
        help="First-run setup: prompt for connection details",
    ).set_defaults(func=cmd_init_wrapper)

    sub.add_parser(
        "status",
        help="Connection, schema version, row counts",
    ).set_defaults(func=cmd_status_wrapper)

    sub.add_parser(
        "tables",
        help="List tables with column and row counts",
    ).set_defaults(func=cmd_tables_wrapper)

    p_schema = sub.add_parser(
        "schema",
        help="Show column definitions for a table",
    )
    p_schema.add_argument("table", help="Table name")
    p_schema.set_defaults(func=cmd_schema_wrapper)

    p_sql = sub.add_parser(
        "sql",
        help="Run an ad-hoc SQL query",
    )
    p_sql.add_argument("query", help="SQL statement(s)")
    p_sql.set_defaults(func=cmd_sql_wrapper)

    p_push = sub.add_parser(
        "push",
        help="Apply pending migrations to Aiven",
    )
    p_push.add_argument(
        "--yes", action="store_true",
        help="Skip confirmation prompt",
    )
    p_push.set_defaults(func=cmd_push_wrapper)

    p_dump = sub.add_parser(
        "dump",
        help="Dump Aiven to a .sql file",
    )
    p_dump.add_argument(
        "path", nargs="?", default=None,
        help="Output file (default: iems-aiven-YYYYMMDD-HHMMSS.sql)",
    )
    p_dump.set_defaults(func=cmd_dump_wrapper)

    p_restore = sub.add_parser(
        "restore",
        help="Load a .sql file into Aiven (destructive — needs --yes)",
    )
    p_restore.add_argument("path", help="Path to .sql file")
    p_restore.add_argument(
        "--yes", action="store_true",
        help="Confirm destructive operation",
    )
    p_restore.set_defaults(func=cmd_restore_wrapper)

    p_config = sub.add_parser("config", help="Manage dbsync config")
    config_sub = p_config.add_subparsers(
        dest="config_command", metavar="<subcommand>", required=True,
    )
    p_config_set = config_sub.add_parser(
        "set-local", help="Set the local Postgres URI",
    )
    p_config_set.add_argument("uri", help="postgresql://user:pass@host:port/db")
    p_config_set.set_defaults(func=cmd_config_wrapper)
    config_sub.add_parser(
        "show", help="Print current config (passwords redacted)",
    ).set_defaults(func=cmd_config_wrapper)

    sub.add_parser(
        "admin",
        help="Interactive CRUD against the local database",
    ).set_defaults(func=cmd_admin_wrapper)

    return parser


# =========================================================
# MAIN
# =========================================================

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())