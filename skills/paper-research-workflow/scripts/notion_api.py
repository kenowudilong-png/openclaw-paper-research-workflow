from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

import requests

from common import clean_text

BASE_URL = "https://api.notion.com/v1"
DATABASE_API_VERSION = os.environ.get("NOTION_DATABASE_API_VERSION", "2022-06-28")
FILE_API_VERSION = os.environ.get("NOTION_FILE_API_VERSION", "2026-03-11")


class NotionAPIError(RuntimeError):
    pass


def notion_token() -> str:
    token = clean_text(os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY"))
    if not token:
        raise NotionAPIError("missing NOTION_TOKEN or NOTION_API_KEY")
    return token


def notion_database_id() -> str:
    database_id = clean_text(os.environ.get("NOTION_PAPER_DB_ID"))
    if not database_id:
        raise NotionAPIError("missing NOTION_PAPER_DB_ID")
    return database_id


def request_json(
    method: str,
    path: str,
    *,
    notion_version: str,
    json_body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    response = requests.request(
        method,
        f"{BASE_URL}{path}",
        headers={
            "Authorization": f"Bearer {notion_token()}",
            "Notion-Version": notion_version,
            "Content-Type": "application/json",
        },
        json=json_body,
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise NotionAPIError(f"{method} {path} failed: {response.status_code} {response.text}")
    return response.json()


def retrieve_database(database_id: str | None = None) -> dict[str, Any]:
    return request_json(
        "GET",
        f"/databases/{database_id or notion_database_id()}",
        notion_version=DATABASE_API_VERSION,
    )


def create_page(database_id: str, properties: dict[str, Any]) -> dict[str, Any]:
    return request_json(
        "POST",
        "/pages",
        notion_version=DATABASE_API_VERSION,
        json_body={"parent": {"database_id": database_id}, "properties": properties},
    )


def update_page(page_id: str, properties: dict[str, Any] | None = None, archived: bool | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if properties:
        body["properties"] = properties
    if archived is not None:
        body["archived"] = archived
    return request_json(
        "PATCH",
        f"/pages/{page_id}",
        notion_version=FILE_API_VERSION,
        json_body=body,
    )


def append_block_children(page_id: str, children: list[dict[str, Any]]) -> dict[str, Any]:
    return request_json(
        "PATCH",
        f"/blocks/{page_id}/children",
        notion_version=FILE_API_VERSION,
        json_body={"children": children},
    )


def create_file_upload(filename: str, content_type: str) -> dict[str, Any]:
    body = {"mode": "single_part", "filename": filename, "content_type": content_type}
    return request_json("POST", "/file_uploads", notion_version=FILE_API_VERSION, json_body=body)


def send_file_upload(file_upload_id: str, file_path: Path, content_type: str) -> dict[str, Any]:
    with file_path.open("rb") as handle:
        response = requests.post(
            f"{BASE_URL}/file_uploads/{file_upload_id}/send",
            headers={
                "Authorization": f"Bearer {notion_token()}",
                "Notion-Version": FILE_API_VERSION,
            },
            files={"file": (file_path.name, handle, content_type)},
            timeout=120,
        )
    if response.status_code >= 400:
        raise NotionAPIError(f"send file upload failed: {response.status_code} {response.text}")
    return response.json()


def retrieve_file_upload(file_upload_id: str) -> dict[str, Any]:
    return request_json("GET", f"/file_uploads/{file_upload_id}", notion_version=FILE_API_VERSION)


def upload_small_file(file_path: str) -> str:
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise NotionAPIError(f"pdf file not found: {path}")
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    created = create_file_upload(path.name, content_type)
    uploaded = send_file_upload(created["id"], path, content_type)
    if uploaded.get("status") != "uploaded":
        uploaded = retrieve_file_upload(created["id"])
    if uploaded.get("status") != "uploaded":
        raise NotionAPIError(f"file upload did not reach uploaded status: {uploaded}")
    return uploaded["id"]
