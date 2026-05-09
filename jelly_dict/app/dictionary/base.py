from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from app.core.models import Language, VocabularyEntry

LookupStatus = Literal[
    "ok",
    "not_found",
    "parse_failed",
    "network_error",
    "rate_limited",
    "unsupported",
]


@dataclass
class LookupResult:
    entry: VocabularyEntry | None = None
    status: LookupStatus = "ok"
    raw_url: str | None = None
    error_detail: str | None = None
    # When the dictionary returned a headword that differs from what the
    # user typed and isn't an obvious variant, parsers can put the
    # canonical form here so the UI can ask "did you mean ...?".
    suggested_word: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "ok" and self.entry is not None


@runtime_checkable
class DictionaryProvider(Protocol):
    def lookup(self, word: str, language: Language) -> LookupResult: ...

    def supports(self, language: Language) -> bool: ...
