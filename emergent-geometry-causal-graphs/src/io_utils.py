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
    with Path(path).expanduser().resolve().open("r", encoding="utf-8") as handle:
        return json.load(handle)
