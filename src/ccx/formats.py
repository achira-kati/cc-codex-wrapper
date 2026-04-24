"""Format-aware deep merge for JSON and TOML file contents."""
import json
import tomllib
from pathlib import Path

import tomli_w

from ccx.merge import deep_merge


def merge_content(portable: str, native: str, target: Path) -> str:
    """Deep-merge two string contents based on the target file's format.

    - `.json` targets: parse both, deep_merge, dump JSON.
    - `.toml` targets: parse both, deep_merge, dump TOML.
    - Unknown formats: `native` replaces `portable` entirely.

    For the semantics of deep_merge, see `ccx.merge.deep_merge`.
    """
    if target.suffix == ".json":
        merged = deep_merge(json.loads(portable), json.loads(native))
        return json.dumps(merged, indent=2, sort_keys=True)
    if target.suffix == ".toml":
        merged = deep_merge(tomllib.loads(portable), tomllib.loads(native))
        return tomli_w.dumps(merged)
    return native
