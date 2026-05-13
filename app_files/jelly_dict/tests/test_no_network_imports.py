"""Guard test: HTTP libraries must live only in app/dictionary/.

Per dev.md §16-A:
  - Network egress is restricted to the dictionary provider layer.
  - Other modules must not import requests / urllib / httpx / aiohttp.
"""
from __future__ import annotations

import ast
import linecache
from pathlib import Path

FORBIDDEN_MODULES = {"requests", "httpx", "aiohttp", "urllib.request"}

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
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_forbidden_import(alias.name):
                        offenders.append(_format_offender(path, rel, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    if _is_forbidden_import(module) or _is_forbidden_import(full_name):
                        offenders.append(_format_offender(path, rel, node.lineno))
    return offenders


def _is_forbidden_import(name: str) -> bool:
    return any(
        name == forbidden or name.startswith(forbidden + ".")
        for forbidden in FORBIDDEN_MODULES
    )


def _format_offender(path: Path, rel: str, line_no: int) -> str:
    line = linecache.getline(str(path), line_no).strip()
    return f"{rel}:{line_no}: {line}"


def test_no_network_imports_outside_dictionary():
    offenders = _scan()
    assert not offenders, "Forbidden network imports found:\n" + "\n".join(offenders)
