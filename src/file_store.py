from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def read_json(path: str | Path) -> dict[str, Any]:
    """Read JSON file into dict."""
    p = Path(path)
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8")))


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    """Write dict into JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
