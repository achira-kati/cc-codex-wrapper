import argparse
import sys

from ccx import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ccx", description="One config source for Claude Code and Codex")
    parser.add_argument("--version", action="version", version=f"ccx {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=False)
    subparsers.add_parser("init", help="Scaffold ~/.ccx/")
    subparsers.add_parser("sync", help="Render canonical → native targets")
    subparsers.add_parser("status", help="Show drift between canonical and targets")
    subparsers.add_parser("restore", help="Restore from a backup snapshot")
    subparsers.add_parser("claude", help="Sync then exec claude")
    subparsers.add_parser("codex", help="Sync then exec codex")
    args, rest = parser.parse_known_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    print(f"ccx: '{args.command}' not yet implemented", file=sys.stderr)
    return 1
