import os
import shutil
import subprocess
import sys
from pathlib import Path

from ccx.commands import sync as cmd_sync
from ccx.scope import Scopes


def run(tool: str, args: list[str], scopes: Scopes, home: Path, project_root: Path | None) -> int:
    if os.environ.get("CCX_SKIP_SYNC") != "1":
        opts = cmd_sync.SyncOptions(quiet=True)
        rc = cmd_sync.run(scopes, home=home, project_root=project_root, opts=opts)
        if rc != 0:
            return rc

    path = shutil.which(tool)
    if path is None:
        print(f"ccx: '{tool}' not found on PATH", file=sys.stderr)
        return 127

    if os.environ.get("CCX_TEST_EXEC") == "1":
        proc = subprocess.run([path] + args)
        return proc.returncode

    os.execvp(path, [path] + args)
    return 0  # unreachable
