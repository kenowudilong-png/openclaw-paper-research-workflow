#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import sys

from common import DOWNLOAD_DIR, OUTPUT_DIR, RESULTS_DIR, ensure_dir, print_json


def module_ready(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    ensure_dir(OUTPUT_DIR)
    ensure_dir(DOWNLOAD_DIR)
    ensure_dir(RESULTS_DIR)
    print_json(
        {
            "success": True,
            "python": sys.executable,
            "paths": {
                "output_dir": str(OUTPUT_DIR),
                "download_dir": str(DOWNLOAD_DIR),
                "results_dir": str(RESULTS_DIR),
            },
            "deps": {
                "scholarly": module_ready("scholarly"),
                "scidownl": module_ready("scidownl"),
                "requests": module_ready("requests"),
            },
            "env": {
                "notion_token_configured": bool(os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")),
                "notion_database_configured": bool(os.environ.get("NOTION_PAPER_DB_ID")),
                "http_proxy_configured": bool(os.environ.get("HTTP_PROXY")),
                "https_proxy_configured": bool(os.environ.get("HTTPS_PROXY")),
            },
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
