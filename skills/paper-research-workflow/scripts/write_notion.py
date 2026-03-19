#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import as_authors, clean_text, load_json_input, print_json, safe_int
from notion_api import (
    NotionAPIError,
    append_block_children,
    create_page,
    notion_database_id,
    retrieve_database,
    update_page,
    upload_small_file,
)

FIELD_ALIASES = {
    "title": ["论文标题", "标题", "Title", "Name", "工具名称"],
    "authors": ["作者", "Authors"],
    "year": ["发表年份", "Year"],
    "doi": ["DOI", "来源链接", "URL", "链接"],
    "journal": ["期刊/会议", "Journal", "Venue", "分类"],
    "tags": ["研究领域", "标签", "Tags", "Topics"],
    "abstract": ["摘要", "Abstract", "详情介绍"],
    "ai_summary": ["AI 总结", "AI总结", "AI Summary", "Summary", "一句话介绍"],
    "relevance_score": ["相关性评分", "评分", "Score"],
}

FILES_ALIASES = ["PDF", "论文PDF", "附件", "Attachments", "Files", "File"]


def find_property(schema: dict[str, Any], logical_key: str) -> tuple[str | None, dict[str, Any] | None]:
    for alias in FIELD_ALIASES.get(logical_key, []):
        if alias in schema:
            return alias, schema[alias]
    if logical_key == "title":
        for name, meta in schema.items():
            if meta.get("type") == "title":
                return name, meta
    return None, None


def find_files_property(schema: dict[str, Any]) -> str | None:
    for alias in FILES_ALIASES:
        if alias in schema and schema[alias].get("type") == "files":
            return alias
    for name, meta in schema.items():
        if meta.get("type") == "files":
            return name
    return None


def build_rich_text(text: str) -> list[dict[str, Any]]:
    return [{"text": {"content": text[:2000]}}] if text else []


def guess_category(paper: dict[str, Any], schema: dict[str, Any]) -> str:
    category_meta = schema.get("分类")
    options = {
        item.get("name")
        for item in (((category_meta or {}).get("select") or {}).get("options") or [])
        if item.get("name")
    }
    text = " ".join(
        [
            clean_text(paper.get("title")),
            clean_text(paper.get("journal")),
            clean_text(paper.get("search_keyword")),
            " ".join(clean_text(tag) for tag in paper.get("tags", []) if clean_text(tag)),
        ]
    ).lower()
    preferred = "AI/自动化" if any(key in text for key in ["ai", "agent", "llm", "gpt", "模型"]) else "其他"
    if preferred in options:
        return preferred
    if "其他" in options:
        return "其他"
    return next(iter(options), "")


def build_detail_text(paper: dict[str, Any]) -> str:
    parts = [
        f"标题：{clean_text(paper.get('title'))}" if clean_text(paper.get("title")) else "",
        f"作者：{', '.join(as_authors(paper.get('authors')))}" if as_authors(paper.get("authors")) else "",
        f"年份：{paper.get('year')}" if paper.get("year") else "",
        f"期刊/会议：{clean_text(paper.get('journal'))}" if clean_text(paper.get("journal")) else "",
        f"DOI/链接：{clean_text(paper.get('doi') or paper.get('url'))}" if clean_text(paper.get("doi") or paper.get("url")) else "",
        f"关键词：{clean_text(paper.get('search_keyword'))}" if clean_text(paper.get("search_keyword")) else "",
        f"PDF路径：{clean_text(paper.get('pdf_path'))}" if clean_text(paper.get("pdf_path")) else "",
        "",
        clean_text(paper.get("abstract")),
    ]
    return "\n".join(part for part in parts if part).strip()


def build_property(meta: dict[str, Any], value: Any) -> dict[str, Any] | None:
    prop_type = meta.get("type")
    if prop_type == "title":
        text = clean_text(value, 2000)
        return {"title": build_rich_text(text)} if text else None
    if prop_type == "rich_text":
        text = clean_text(value, 2000)
        return {"rich_text": build_rich_text(text)} if text else None
    if prop_type == "number":
        number = safe_int(value, default=-1)
        return {"number": None if number < 0 else number}
    if prop_type == "url":
        text = clean_text(value)
        if text and not text.startswith(("http://", "https://")) and "/" in text:
            text = f"https://doi.org/{text}"
        return {"url": text or None}
    if prop_type == "select":
        text = clean_text(value, 100)
        return {"select": {"name": text}} if text else None
    if prop_type == "multi_select":
        values = value if isinstance(value, list) else [value]
        items = [{"name": clean_text(item, 100)} for item in values if clean_text(item)]
        return {"multi_select": items} if items else None
    return None


def attach_pdf(page_id: str, schema: dict[str, Any], pdf_path: str) -> dict[str, Any]:
    path = Path(pdf_path).expanduser()
    if not path.exists():
        return {"attached": False, "mode": "", "warning": f"pdf_path not found: {path}"}

    file_upload_id = upload_small_file(str(path))
    files_property = find_files_property(schema)
    if files_property:
        update_page(
            page_id,
            properties={
                files_property: {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {"id": file_upload_id},
                            "name": path.name,
                        }
                    ]
                }
            },
        )
        return {"attached": True, "mode": "files-property", "file_upload_id": file_upload_id}

    append_block_children(
        page_id,
        children=[
            {
                "object": "block",
                "type": "file",
                "file": {
                    "caption": [{"type": "text", "text": {"content": path.name}}],
                    "type": "file_upload",
                    "file_upload": {"id": file_upload_id},
                },
            }
        ],
    )
    return {"attached": True, "mode": "file-block", "file_upload_id": file_upload_id}


def main() -> int:
    parser = argparse.ArgumentParser(description="Write one paper record into Notion.")
    parser.add_argument("--paper-json")
    parser.add_argument("--input-file")
    args = parser.parse_args()

    try:
        paper = load_json_input(args.paper_json, args.input_file)
        database = retrieve_database()
        schema = database.get("properties") or {}
        database_id = notion_database_id()
    except (ValueError, NotionAPIError) as exc:
        print_json({"success": False, "error": clean_text(exc)})
        return 1

    summary = clean_text(paper.get("ai_summary")) or clean_text(paper.get("title"))
    detail_text = build_detail_text(paper)
    category = guess_category(paper, schema)

    logical_values = {
        "title": paper.get("title"),
        "authors": ", ".join(as_authors(paper.get("authors"))),
        "year": paper.get("year"),
        "doi": paper.get("doi") or paper.get("url"),
        "journal": category or paper.get("journal"),
        "tags": paper.get("tags") or [],
        "abstract": detail_text,
        "ai_summary": summary,
        "relevance_score": paper.get("relevance_score"),
    }

    properties: dict[str, Any] = {}
    used_properties: list[str] = []
    for logical_key, value in logical_values.items():
        name, meta = find_property(schema, logical_key)
        if not name or not meta:
            continue
        prop = build_property(meta, value)
        if prop is None:
            continue
        properties[name] = prop
        used_properties.append(name)

    if not properties:
        print_json({"success": False, "error": "no compatible Notion properties found"})
        return 1

    try:
        page = create_page(database_id, properties)
        attachment = {"attached": False, "mode": ""}
        if clean_text(paper.get("pdf_path")):
            attachment = attach_pdf(page["id"], schema, clean_text(paper.get("pdf_path")))
    except NotionAPIError as exc:
        print_json({"success": False, "error": clean_text(exc)})
        return 1

    payload = {
        "success": True,
        "page_id": page.get("id"),
        "url": page.get("url"),
        "used_properties": used_properties,
        "pdf_attached": attachment.get("attached", False),
        "pdf_attach_mode": attachment.get("mode", ""),
    }
    if attachment.get("warning"):
        payload["warning"] = attachment["warning"]
    print_json(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
