from __future__ import annotations

import json
import unicodedata
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Language = Literal["en", "ja"]
SourceProvider = Literal["naver_en", "naver_ja", "manual", "naver_api", "unknown"]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Example:
    source_text: str = ""
    source_text_plain: str = ""
    translation_ko: str | None = None
    order: int = 0


@dataclass
class SubSense:
    label: str = ""
    gloss: str = ""
    examples: list[Example] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)


@dataclass
class Sense:
    number: int = 0
    gloss: str = ""
    sub_senses: list[SubSense] = field(default_factory=list)


@dataclass
class MeaningGroup:
    pos: str = ""
    senses: list[Sense] = field(default_factory=list)


@dataclass
class VocabularyEntry:
    language: Language = "en"
    word: str = ""
    reading: str | None = None
    pronunciation_audio_url: str | None = None
    part_of_speech: list[str] = field(default_factory=list)
    meaning_groups: list[MeaningGroup] = field(default_factory=list)
    meanings_summary: str = ""
    examples_flat: list[Example] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    memo: str = ""
    source_url: str | None = None
    source_provider: SourceProvider = "unknown"
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now_utc)
    updated_at: str = field(default_factory=_now_utc)

    def word_key(self) -> str:
        return normalize_word_key(self.word, self.language)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VocabularyEntry:
        meaning_groups = [
            MeaningGroup(
                pos=mg.get("pos", ""),
                senses=[
                    Sense(
                        number=s.get("number", 0),
                        gloss=s.get("gloss", ""),
                        sub_senses=[
                            SubSense(
                                label=ss.get("label", ""),
                                gloss=ss.get("gloss", ""),
                                examples=[Example(**ex) for ex in ss.get("examples", [])],
                                synonyms=list(ss.get("synonyms", [])),
                                antonyms=list(ss.get("antonyms", [])),
                            )
                            for ss in s.get("sub_senses", [])
                        ],
                    )
                    for s in mg.get("senses", [])
                ],
            )
            for mg in data.get("meaning_groups", [])
        ]
        examples_flat = [Example(**ex) for ex in data.get("examples_flat", [])]
        return cls(
            language=data.get("language", "en"),
            word=data.get("word", ""),
            reading=data.get("reading"),
            pronunciation_audio_url=data.get("pronunciation_audio_url"),
            part_of_speech=list(data.get("part_of_speech", [])),
            meaning_groups=meaning_groups,
            meanings_summary=data.get("meanings_summary", ""),
            examples_flat=examples_flat,
            synonyms=list(data.get("synonyms", [])),
            antonyms=list(data.get("antonyms", [])),
            tags=list(data.get("tags", [])),
            memo=data.get("memo", ""),
            source_url=data.get("source_url"),
            source_provider=data.get("source_provider", "unknown"),
            id=data.get("id", _new_id()),
            created_at=data.get("created_at", _now_utc()),
            updated_at=data.get("updated_at", _now_utc()),
        )

    @classmethod
    def from_json(cls, payload: str) -> VocabularyEntry:
        return cls.from_dict(json.loads(payload))

    def touch(self) -> None:
        self.updated_at = _now_utc()


def normalize_word_key(word: str, language: Language) -> str:
    """Canonical key for duplicate detection and cache lookup."""
    text = (word or "").strip()
    if language == "en":
        return text.lower()
    return unicodedata.normalize("NFKC", text)


def build_meanings_summary(entry: VocabularyEntry) -> str:
    """Build the compact summary line shown on Anki back / Excel.

    Format: "[<pos>] 1. <gloss1> 2. <gloss2> ..."
    Falls back to the first sub-sense gloss when the sense gloss is empty.
    Truncates each gloss at the first ';' or ',' token to keep it short.
    """
    if not entry.meaning_groups:
        return ""

    primary = entry.meaning_groups[0]
    pos_label = primary.pos.strip()
    parts: list[str] = []
    for sense in primary.senses:
        gloss = (sense.gloss or "").strip()
        if not gloss and sense.sub_senses:
            gloss = (sense.sub_senses[0].gloss or "").strip()
        if not gloss:
            continue
        gloss = _short_gloss(gloss)
        number = sense.number if sense.number else len(parts) + 1
        parts.append(f"{number}. {gloss}")

    body = " ".join(parts)
    if not body:
        # No usable senses -> return empty rather than the bare POS,
        # so callers can tell that nothing was actually parsed.
        return ""
    if pos_label:
        return f"[{pos_label}] {body}"
    return body


def _short_gloss(text: str) -> str:
    for sep in (";", ",", "/"):
        if sep in text:
            text = text.split(sep, 1)[0]
    return text.strip().rstrip(".")


def first_meaning_hint(entry: VocabularyEntry, limit: int = 40) -> str:
    """Return the first Korean gloss in the entry, suitable for compact
    list views (recent words, wordbook rows). Falls back to the entry's
    `meanings_summary` after stripping the POS prefix and any leading
    sense numbering. Pure function, no side effects."""
    import re

    for group in entry.meaning_groups:
        for sense in group.senses:
            if sense.gloss:
                return _trim_hint(sense.gloss, limit=limit)
            for sub in sense.sub_senses:
                if sub.gloss:
                    return _trim_hint(sub.gloss, limit=limit)
    if entry.meanings_summary:
        stripped = re.sub(r"^\[[^\]]+\]\s*", "", entry.meanings_summary)
        # Tolerate the variants " 1.", "1 .", "1.1.", " 1 . 1 . " etc.
        stripped = re.sub(r"^\s*(?:\d+\s*\.\s*)+", "", stripped)
        return _trim_hint(stripped, limit=limit)
    return ""


def _trim_hint(text: str, limit: int = 40) -> str:
    text = (text or "").strip().rstrip(".")
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text


def collect_examples_flat(entry: VocabularyEntry) -> list[Example]:
    """Flatten all SubSense examples into a single ordered list."""
    flat: list[Example] = []
    order = 0
    for mg in entry.meaning_groups:
        for sense in mg.senses:
            for sub in sense.sub_senses:
                for ex in sub.examples:
                    flat.append(
                        Example(
                            source_text=ex.source_text,
                            source_text_plain=ex.source_text_plain,
                            translation_ko=ex.translation_ko,
                            order=order,
                        )
                    )
                    order += 1
    return flat
