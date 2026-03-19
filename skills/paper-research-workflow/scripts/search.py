#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from typing import Any

from common import as_authors, clean_text, print_json, safe_int, save_json, truthy


def search_semantic_scholar(query: str, limit: int, year_from: int, year_to: int) -> list[dict[str, Any]]:
    fields = ",".join(
        [
            "title",
            "authors",
            "year",
            "abstract",
            "citationCount",
            "externalIds",
            "url",
            "venue",
            "openAccessPdf",
        ]
    )
    params = urllib.parse.urlencode({"query": query, "limit": limit, "fields": fields})
    request = urllib.request.Request(
        f"https://api.semanticscholar.org/graph/v1/paper/search?{params}",
        headers={"User-Agent": "OpenClaw paper-research-workflow/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))

    papers: list[dict[str, Any]] = []
    for item in payload.get("data", []):
        year = safe_int(item.get("year"))
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        external_ids = item.get("externalIds") or {}
        open_access_pdf = item.get("openAccessPdf") or {}
        papers.append(
            {
                "title": clean_text(item.get("title")),
                "authors": [clean_text(a.get("name")) for a in item.get("authors", []) if clean_text(a.get("name"))],
                "year": year,
                "abstract": clean_text(item.get("abstract")),
                "doi": clean_text(external_ids.get("DOI")),
                "citation_count": safe_int(item.get("citationCount")),
                "url": clean_text(item.get("url")),
                "journal": clean_text(item.get("venue")),
                "open_access_pdf": clean_text(open_access_pdf.get("url")),
                "source": "semantic-scholar",
            }
        )
    return papers


def search_scholarly(query: str, limit: int, year_from: int, year_to: int) -> list[dict[str, Any]]:
    from scholarly import ProxyGenerator, scholarly

    if truthy(os.environ.get("SCHOLARLY_USE_FREE_PROXIES", "0")):
        proxy = ProxyGenerator()
        if proxy.FreeProxies():
            scholarly.use_proxy(proxy)

    papers: list[dict[str, Any]] = []
    for item in scholarly.search_pubs(query):
        if len(papers) >= limit:
            break
        bib = item.get("bib") or {}
        year = safe_int(bib.get("pub_year"))
        if year_from and year and year < year_from:
            continue
        if year_to and year and year > year_to:
            continue
        papers.append(
            {
                "title": clean_text(bib.get("title")),
                "authors": as_authors(bib.get("author")),
                "year": year,
                "abstract": clean_text(bib.get("abstract")),
                "doi": "",
                "citation_count": safe_int(item.get("num_citations")),
                "url": clean_text(item.get("pub_url") or item.get("eprint_url")),
                "journal": clean_text(bib.get("venue") or bib.get("journal")),
                "open_access_pdf": clean_text(item.get("eprint_url")),
                "source": "scholar",
            }
        )
    return papers


def main() -> int:
    parser = argparse.ArgumentParser(description="Search academic papers.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--year-from", type=int, default=0)
    parser.add_argument("--year-to", type=int, default=0)
    parser.add_argument("--prefer", choices=["auto", "scholar", "semantic"], default="auto")
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    strategies = {"scholar": ["scholar"], "semantic": ["semantic"], "auto": ["scholar", "semantic"]}[args.prefer]
    papers: list[dict[str, Any]] = []
    warnings: list[str] = []
    error = ""
    source_used = ""

    for strategy in strategies:
        try:
            if strategy == "scholar":
                papers = search_scholarly(args.query, args.limit, args.year_from, args.year_to)
                source_used = "scholar"
            else:
                papers = search_semantic_scholar(args.query, args.limit, args.year_from, args.year_to)
                source_used = "semantic-scholar"
            if papers:
                break
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{strategy}_search_failed")
            error = f"{strategy}: {exc}"

    payload: dict[str, Any] = {
        "success": bool(papers),
        "query": args.query,
        "count": len(papers),
        "source": source_used,
        "warnings": warnings,
        "papers": papers[: args.limit],
    }
    if error and not papers:
        payload["error"] = error
    if args.save:
        payload["saved_to"] = save_json(payload, "search")
    print_json(payload)
    return 0 if papers else 1


if __name__ == "__main__":
    raise SystemExit(main())
