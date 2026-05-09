from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from app.core import config

EXCEL_COLUMN_KEYS_DEFAULT = [
    "language",
    "word",
    "reading",
    "part_of_speech",
    "meanings_summary",
    "meanings_detail",
    "examples",
    "example_translations",
    "synonyms",
    "antonyms",
    "tags",
    "memo",
    "source_url",
    "created_at",
    "updated_at",
]


@dataclass
class Settings:
    default_excel_dir: str = ""
    # Per-language target Excel files. Empty string -> auto path under default_excel_dir.
    excel_path_en: str = ""
    excel_path_ja: str = ""
    # Per-language Anki export targets.
    anki_path_en: str = ""
    anki_path_ja: str = ""
    default_anki_export_dir: str = ""
    request_delay_seconds: float = 1.0  # conservative: ~human typing speed
    cache_enabled: bool = True
    duplicate_policy: str = "ask"  # ask|keep_existing|update_existing|merge_examples_and_memo|add_as_new
    excel_columns: list[str] = field(default_factory=lambda: list(EXCEL_COLUMN_KEYS_DEFAULT))
    theme: str = "dark"
    show_preview: bool = False  # default OFF for speed; toggle on to edit details
    default_deck_name: str = "JellyDict"
    language_label_translate: bool = True
    provider: str = "naver_crawler"  # future: naver_api, etc.
    # AnkiConnect (localhost RPC to the Anki desktop addon).
    ankiconnect_enabled: bool = False
    ankiconnect_url: str = "http://127.0.0.1:8765"
    ankiconnect_deck_prefix: str = "JellyDict"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def excel_path_for(self, language: str) -> str:
        from pathlib import Path

        explicit = self.excel_path_ja if language == "ja" else self.excel_path_en
        if explicit:
            return explicit
        base = Path(self.default_excel_dir or str(config.default_excel_dir()))
        name = "vocab_ja.xlsx" if language == "ja" else "vocab_en.xlsx"
        return str(base / name)

    def anki_path_for(self, language: str) -> str:
        from pathlib import Path

        explicit = self.anki_path_ja if language == "ja" else self.anki_path_en
        if explicit:
            return explicit
        base = Path(self.default_anki_export_dir or str(config.default_excel_dir()))
        name = "jelly-dict_ja.apkg" if language == "ja" else "jelly-dict_en.apkg"
        return str(base / name)


def _defaults() -> Settings:
    s = Settings()
    s.default_excel_dir = str(config.default_excel_dir())
    s.default_anki_export_dir = str(config.default_excel_dir())
    return s


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config.settings_path()
        self._cache: Settings | None = None

    def load(self) -> Settings:
        if self._cache is not None:
            return self._cache
        if not self.path.exists():
            self._cache = _defaults()
            self.save(self._cache)
            return self._cache
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Corrupt settings: rebuild from defaults rather than crash.
            self._cache = _defaults()
            self.save(self._cache)
            return self._cache
        merged = _defaults()
        valid_keys = {f.name for f in fields(Settings)}
        for key, value in raw.items():
            if key in valid_keys:
                setattr(merged, key, value)
        self._cache = merged
        return merged

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._cache = settings

    def update(self, **changes: Any) -> Settings:
        current = self.load()
        for key, value in changes.items():
            if hasattr(current, key):
                setattr(current, key, value)
        self.save(current)
        return current
