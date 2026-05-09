"""Debug helper: fetch a Naver dictionary entry URL with WebKit and save HTML.

Usage:
    python scripts/dump_entry.py https://en.dict.naver.com/#/entry/enko/c7e4...
    python scripts/dump_entry.py https://ja.dict.naver.com/#/entry/jako/...

Saves both the rendered HTML and a few key extracted regions to ./.jelly_dict/dump/.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from app.core import config
from app.dictionary.playwright_client import PlaywrightClient


def main(url: str) -> int:
    out_dir = config.runtime_dir() / "dump"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", url)[-80:]
    full_path = out_dir / f"{safe}.html"

    client = PlaywrightClient(headless=True, request_delay_seconds=0.0)
    client.start()
    try:
        # Naver SPA: wait until the dynamic content sits in the DOM.
        html = client.fetch(
            url,
            wait_selector="div.entry_search_word, .entry_title, .entry_section, #content .row",
            timeout_ms=25_000,
        )
    finally:
        client.stop()

    full_path.write_text(html, encoding="utf-8")
    print(f"saved: {full_path}  ({len(html):,} bytes)")
    print()

    # quick text-mode sniff: print every distinct class attribute that
    # contains words like 'mean', 'pron', 'example', 'syn', 'antonym'.
    classes = sorted({
        c.strip()
        for cls in re.findall(r'class="([^"]+)"', html)
        for c in cls.split()
        if any(k in c.lower() for k in ("mean", "pron", "example", "syn", "antonym", "audio", "ruby", "exam"))
    })
    print("--- candidate classes ---")
    for c in classes:
        print(f"  .{c}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
