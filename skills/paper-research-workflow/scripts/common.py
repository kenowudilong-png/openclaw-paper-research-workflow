from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = SKILL_DIR / "output"
ENV_FILES = [
    SKILL_DIR / ".env",
    Path.home() / ".openclaw" / "paper-research.env",
    Path.home() / ".openclaw" / ".env",
]


def load_env_files() -> None:
    for env_path in ENV_FILES:
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_files()

OUTPUT_DIR = Path(os.environ.get("PAPER_WORKFLOW_DATA_DIR", str(DEFAULT_OUTPUT_DIR))).expanduser()
DOWNLOAD_DIR = Path(os.environ.get("PAPER_DOWNLOAD_DIR", str(OUTPUT_DIR / "papers"))).expanduser()
RESULTS_DIR = Path(os.environ.get("PAPER_RESULTS_DIR", str(OUTPUT_DIR / "results"))).expanduser()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def save_json(payload: dict[str, Any], prefix: str) -> str:
    ensure_dir(RESULTS_DIR)
    target = RESULTS_DIR / f"{prefix}-{utc_timestamp()}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


def clean_text(value: Any, limit: int | None = None) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value if item is not None)
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text[:limit] if limit is not None else text


def as_authors(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]
    text = clean_text(value)
    if not text:
        return []
    if " and " in text:
        return [clean_text(part) for part in text.split(" and ") if clean_text(part)]
    if "," in text:
        return [clean_text(part) for part in text.split(",") if clean_text(part)]
    return [text]


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def slugify(text: str, limit: int = 120) -> str:
    normalized = re.sub(r"[^\w\s.-]", "", text, flags=re.UNICODE)
    normalized = re.sub(r"[-\s]+", "-", normalized).strip("-_.")
    return (normalized or "paper")[:limit]


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_json_input(json_text: str | None, file_path: str | None) -> dict[str, Any]:
    if json_text:
        return json.loads(json_text)
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    raise ValueError("must provide --paper-json or --input-file")
