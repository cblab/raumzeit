from __future__ import annotations

from copy import deepcopy
from pathlib import Path



def _parse_scalar(raw: str):
    text = raw.strip()
    if text in {"", "null", "Null", "NULL", "~"}:
        return None
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False

    if (text.startswith("\"") and text.endswith("\"")) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    return text



def _parse_inline_list(raw: str) -> list:
    body = raw.strip()[1:-1].strip()
    if not body:
        return []
    return [_parse_scalar(part.strip()) for part in body.split(",")]



def _load_simple_yaml(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    out: dict = {}
    i = 0

    while i < len(lines):
        line = lines[i]
        line = line.split("#", 1)[0].rstrip()
        if not line.strip():
            i += 1
            continue

        if ":" not in line:
            raise ValueError(f"Invalid YAML line in {path}: {line}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value == "":
            items = []
            i += 1
            while i < len(lines):
                sub = lines[i].split("#", 1)[0].rstrip()
                if not sub.strip():
                    i += 1
                    continue
                if not sub.startswith("  - "):
                    break
                items.append(_parse_scalar(sub[4:].strip()))
                i += 1
            out[key] = items
            continue

        if value.startswith("[") and value.endswith("]"):
            out[key] = _parse_inline_list(value)
        else:
            out[key] = _parse_scalar(value)

        i += 1

    return out



def _merge_dicts(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged



def _load_config_recursive(path: Path) -> dict:
    raw = _load_simple_yaml(path)

    if not isinstance(raw, dict):
        raise ValueError(f"Config must contain a mapping at top-level: {path}")

    inherits = raw.pop("inherits", None)
    if not inherits:
        return raw

    parent_path = (path.parent / str(inherits)).resolve()
    parent_config = _load_config_recursive(parent_path)
    return _merge_dicts(parent_config, raw)



def load_config(path: str | Path) -> dict:
    """Load a YAML config and apply optional inheritance via `inherits`."""

    resolved = Path(path).expanduser().resolve()
    return _load_config_recursive(resolved)
