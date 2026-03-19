#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SKILL_NAME = "paper-research-workflow"
DATABASE_API_VERSION = "2022-06-28"
FILE_API_VERSION = "2026-03-11"


def parse_database_id(raw: str) -> str:
    text = raw.strip()
    uuid_match = re.search(r"([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})", text)
    if not uuid_match:
        raise ValueError(f"unable to parse Notion database id from: {raw}")
    value = uuid_match.group(1).replace("-", "")
    return f"{value[0:8]}-{value[8:12]}-{value[12:16]}-{value[16:20]}-{value[20:32]}"


def validate_database(token: str, database_id: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": DATABASE_API_VERSION},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion validation failed: {exc.code} {body}") from exc


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_skill(repo_root: Path, target_dir: Path) -> Path:
    source = repo_root / "skills" / SKILL_NAME
    destination = target_dir / SKILL_NAME
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", ".env"),
    )
    return destination


def configure_openclaw(
    openclaw_json_path: Path,
    token: str | None,
    database_url: str | None,
    database_id: str | None,
    http_proxy: str | None,
    https_proxy: str | None,
) -> dict[str, Any]:
    payload = load_json(openclaw_json_path)
    payload.setdefault("skills", {})
    payload["skills"].setdefault("entries", {})
    entry = payload["skills"]["entries"].setdefault(SKILL_NAME, {})
    entry["enabled"] = True
    env = entry.setdefault("env", {})

    if token:
        env["NOTION_TOKEN"] = token
        env["NOTION_API_KEY"] = token
    if database_url:
        env["NOTION_PAPER_DB_URL"] = database_url
    if database_id:
        env["NOTION_PAPER_DB_ID"] = database_id
    env["NOTION_DATABASE_API_VERSION"] = DATABASE_API_VERSION
    env["NOTION_FILE_API_VERSION"] = FILE_API_VERSION

    if http_proxy:
        env["HTTP_PROXY"] = http_proxy
    if https_proxy:
        env["HTTPS_PROXY"] = https_proxy

    save_json(openclaw_json_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the paper research skill into OpenClaw.")
    parser.add_argument("--openclaw-home", default=os.environ.get("OPENCLAW_HOME", str(Path.home() / ".openclaw")))
    parser.add_argument("--workspace", help="Explicit OpenClaw workspace path when using --target workspace")
    parser.add_argument("--target", choices=["managed", "workspace"], default="managed")
    parser.add_argument("--token", help="Notion integration token")
    parser.add_argument("--database-url", help="Notion database URL")
    parser.add_argument("--database-id", help="Notion database id")
    parser.add_argument("--http-proxy")
    parser.add_argument("--https-proxy")
    parser.add_argument("--bootstrap", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    openclaw_home = Path(args.openclaw_home).expanduser()
    openclaw_json_path = openclaw_home / "openclaw.json"
    if args.target == "managed":
        skills_root = openclaw_home / "skills"
    else:
        workspace = Path(args.workspace).expanduser() if args.workspace else openclaw_home / "workspace"
        skills_root = workspace / "skills"

    skills_root.mkdir(parents=True, exist_ok=True)
    installed_path = copy_skill(repo_root, skills_root)

    notion_db_id = args.database_id
    if args.database_url and not notion_db_id:
        notion_db_id = parse_database_id(args.database_url)
    if notion_db_id and args.token:
        validate_database(args.token, notion_db_id)

    configure_openclaw(
        openclaw_json_path=openclaw_json_path,
        token=args.token,
        database_url=args.database_url,
        database_id=notion_db_id,
        http_proxy=args.http_proxy,
        https_proxy=args.https_proxy,
    )

    if args.bootstrap:
        subprocess.run(["bash", str(installed_path / "scripts" / "bootstrap.sh")], check=True)

    result = {
        "installed_skill_path": str(installed_path),
        "openclaw_json": str(openclaw_json_path),
        "target": args.target,
        "configured_database_id": notion_db_id,
        "bootstrap": args.bootstrap,
        "note": "Start a new OpenClaw session after install so the new skill snapshot is picked up.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
