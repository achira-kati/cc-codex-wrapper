import argparse
import os
import sys
from pathlib import Path

from ccx import __version__
from ccx.commands import init as cmd_init
from ccx.commands import sync as cmd_sync
from ccx.scope import discover


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ccx", description="One config source for Claude Code and Codex")
    parser.add_argument("--version", action="version", version=f"ccx {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=False)
    subparsers.add_parser("init", help="Scaffold ~/.ccx/")

    sync_p = subparsers.add_parser("sync", help="Render canonical -> native targets")
    sync_p.add_argument("--dry-run", action="store_true")
    sync_p.add_argument("--force", action="store_true")
    sync_p.add_argument("--check", action="store_true", help="Exit non-zero if targets are stale")
    sync_p.add_argument("--quiet", action="store_true")

    subparsers.add_parser("status", help="Show drift between canonical and targets")
    subparsers.add_parser("restore", help="Restore from a backup snapshot")
    subparsers.add_parser("claude", help="Sync then exec claude")
    subparsers.add_parser("codex", help="Sync then exec codex")

    args, rest = parser.parse_known_args(argv)

    home = Path(os.environ["HOME"])
    scopes = discover()
    project_root = scopes.project.parent if scopes.project else None

    if args.command == "init":
        return cmd_init.run(scopes.user)

    if args.command == "sync":
        # --check is handled in Task 14; for now ignore if passed alone
        opts = cmd_sync.SyncOptions(dry_run=args.dry_run, force=args.force, quiet=args.quiet)
        return cmd_sync.run(scopes, home=home, project_root=project_root, opts=opts)

    if args.command is None:
        parser.print_help()
        return 0

    print(f"ccx: '{args.command}' not yet implemented", file=sys.stderr)
    return 1
