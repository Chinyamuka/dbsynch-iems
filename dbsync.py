#!/usr/bin/env python3
"""
dbsync — local database manager for IEMS on Aiven.

Usage:
    dbsync init             First-run setup
    dbsync status           Show connection, schema version, row counts

Run 'dbsync <command> --help' for details.
"""

import argparse
import sys

import config as cfg
from commands import init as cmd_init
from commands import status as cmd_status


BOLD  = "\033[1m"
RED   = "\033[31m"
RESET = "\033[0m"


# =========================================================
# COMMAND REGISTRY
# =========================================================

def cmd_init_wrapper(args) -> int:
    return cmd_init.run()


def cmd_status_wrapper(args) -> int:
    try:
        config = cfg.load()
    except FileNotFoundError as e:
        print(f"{RED}{e}{RESET}", file=sys.stderr)
        return 1
    return cmd_status.run(config)


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
        help="Show connectivity, schema version, and row counts",
    ).set_defaults(func=cmd_status_wrapper)

    return parser


# =========================================================
# MAIN
# =========================================================

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
