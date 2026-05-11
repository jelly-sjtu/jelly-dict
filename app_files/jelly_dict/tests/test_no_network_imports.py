"""Guard test: HTTP libraries must live only in app/dictionary/.

Per dev.md §16-A:
  - Network egress is restricted to the dictionary provider layer.
  - Other modules must not import requests / urllib / httpx / aiohttp.
"""
from __future__ import annotations

import re
from pathlib import Path

FORBIDDEN_PATTERNS = [
    re.compile(r"^\s*import\s+requests\b"),
    re.compile(r"^\s*from\s+requests\b"),
    re.compile(r"^\s*import\s+httpx\b"),
    re.compile(r"^\s*from\s+httpx\b"),
    re.compile(r"^\s*import\s+aiohttp\b"),
    re.compile(r"^\s*from\s+aiohttp\b"),
    re.compile(r"^\s*from\s+urllib\.request\b"),
    re.compile(r"^\s*import\s+urllib\.request\b"),
]

ALLOWED_PREFIXES = (
    "app/dictionary/",
    # AnkiConnect client talks only to 127.0.0.1:8765 on the user's
    # own machine — it's local IPC, not external network egress.
    "app/anki/ankiconnect_client.py",
    # VOICEVOX talks only to 127.0.0.1:50021 (locally-installed engine).
    "app/anki/tts/voicevox_provider.py",
    # Google Cloud Vision OCR — only triggered when the user explicitly
    # configures their own API key in the settings.
    "app/ocr/google_vision.py",
)


def _scan() -> list[str]:
    root = Path(__file__).resolve().parents[1] / "app"
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root.parent).as_posix()
        if any(rel.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.match(line):
                    offenders.append(f"{rel}:{line_no}: {line.strip()}")
    return offenders


def test_no_network_imports_outside_dictionary():
    offenders = _scan()
    assert not offenders, "Forbidden network imports found:\n" + "\n".join(offenders)
