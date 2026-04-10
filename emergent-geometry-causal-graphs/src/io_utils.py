from __future__ import annotations

import json
from pathlib import Path
from typing import Any



def ensure_parent_dir(path: str | Path) -> None:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)



def save_json(path: str | Path, payload: Any) -> None:
    out_path = Path(path).expanduser().resolve()
    ensure_parent_dir(out_path)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)



def load_json(path: str | Path) -> Any:
    in_path = Path(path).expanduser().resolve()
    try:
        raw_text = in_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Failed to read JSON file: {in_path}") from exc

    if not raw_text.strip():
        raise ValueError(f"JSON file is empty: {in_path}")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in file {in_path}: {exc.msg} (line {exc.lineno}, column {exc.colno})"
        ) from exc
