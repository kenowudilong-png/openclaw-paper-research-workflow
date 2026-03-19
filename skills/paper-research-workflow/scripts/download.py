#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from common import DOWNLOAD_DIR, clean_text, ensure_dir, print_json, slugify


def resolve_scidownl_bin() -> str | None:
    venv_bin = Path(sys.executable).resolve().with_name("scidownl")
    if venv_bin.exists():
        return str(venv_bin)
    return shutil.which("scidownl")


def download_direct_pdf(pdf_url: str, target: Path, timeout: int) -> dict:
    request = urllib.request.Request(
        pdf_url,
        headers={
            "User-Agent": "Mozilla/5.0 OpenClaw paper-research-workflow",
            "Accept": "application/pdf,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    target.write_bytes(data)
    return {"success": True, "filepath": str(target), "error": "", "method": "direct-pdf-url"}


def download_with_scidownl(doi: str, pmid: str, title: str, target: Path, proxy: str | None, timeout: int) -> dict:
    scidownl_bin = resolve_scidownl_bin()
    if not scidownl_bin:
        return {"success": False, "filepath": "", "error": "scidownl not found", "method": "scidownl"}

    command = [scidownl_bin, "download"]
    if doi:
        command.extend(["--doi", doi])
    elif pmid:
        command.extend(["--pmid", pmid])
    elif title:
        command.extend(["--title", title])
    else:
        return {"success": False, "filepath": "", "error": "need doi, pmid, or title", "method": "scidownl"}
    command.extend(["--out", str(target)])
    if proxy:
        command.extend(["--proxy", proxy])

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return {"success": False, "filepath": "", "error": f"download timed out after {timeout}s", "method": "scidownl"}

    if target.exists() and target.stat().st_size > 0:
        return {"success": True, "filepath": str(target), "error": "", "method": "scidownl"}
    return {
        "success": False,
        "filepath": "",
        "error": clean_text(result.stderr or result.stdout or "download failed"),
        "method": "scidownl",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Download paper PDFs.")
    parser.add_argument("--doi", default="")
    parser.add_argument("--pmid", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--pdf-url", default="")
    parser.add_argument("--proxy", default=os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--output-dir", default=str(DOWNLOAD_DIR))
    args = parser.parse_args()

    output_dir = ensure_dir(Path(args.output_dir).expanduser())
    stem = args.doi or args.pmid or args.title or args.pdf_url or "paper"
    target = output_dir / f"{slugify(stem)}.pdf"

    if target.exists() and target.stat().st_size > 0:
        print_json({"success": True, "filepath": str(target), "error": "", "method": "cached"})
        return 0

    direct_error = ""
    if args.pdf_url:
        try:
            result = download_direct_pdf(args.pdf_url, target, args.timeout)
            print_json(result)
            return 0
        except Exception as exc:  # noqa: BLE001
            direct_error = clean_text(exc)

    result = download_with_scidownl(args.doi, args.pmid, args.title, target, args.proxy or None, args.timeout)
    if direct_error and not result["success"]:
        result["error"] = clean_text(f"direct pdf failed: {direct_error}; scidownl failed: {result['error']}")
    print_json(result)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
