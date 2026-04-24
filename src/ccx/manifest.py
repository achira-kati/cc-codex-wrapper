import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Manifest:
    entries: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(entries=dict(data.get("entries", {})))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"entries": self.entries}, indent=2, sort_keys=True))

    def record(self, target: Path, sha256: str) -> None:
        self.entries[str(target)] = sha256

    def is_managed(self, target: Path) -> bool:
        recorded = self.entries.get(str(target))
        if recorded is None:
            return False
        if not target.exists() or target.is_symlink():
            return False
        return self.hash_file(target) == recorded

    def orphans(self, desired: set[Path]) -> set[Path]:
        desired_str = {str(p) for p in desired}
        return {Path(s) for s in self.entries if s not in desired_str}

    @staticmethod
    def hash_file(path: Path) -> str:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
