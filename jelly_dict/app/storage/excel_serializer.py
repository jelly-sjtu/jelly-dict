"""Cell-level serialization between VocabularyEntry and Excel rows.

Pure conversion helpers + style constants. No IO, no openpyxl Workbook
manipulation — that lives in `excel_writer.py` and `excel_reader.py`.
"""
from __future__ import annotations

from typing import Iterable

from openpyxl.styles import Font, PatternFill

from app.core.models import (
    Example,
    MeaningGroup,
    VocabularyEntry,
    build_meanings_summary,
    collect_examples_flat,
)

SHEET_NAME = "Vocabulary"

COLUMN_LABELS: dict[str, str] = {
    "language": "Language",
    "word": "Word",
    "reading": "Reading/Pronunciation",
    "part_of_speech": "Part of Speech",
    "meanings_summary": "Meanings",
    "meanings_detail": "Meanings Detail",
    "examples": "Examples",
    "example_translations": "Example Translations",
    "synonyms": "Synonyms",
    "antonyms": "Antonyms",
    "tags": "Tags",
    "memo": "Memo",
    "source_url": "Source URL",
    "created_at": "Created At",
    "updated_at": "Updated At",
}

COLUMN_WIDTHS: dict[str, int] = {
    "language": 8,
    "word": 18,
    "reading": 20,
    "part_of_speech": 14,
    "meanings_summary": 40,
    "meanings_detail": 50,
    "examples": 50,
    "example_translations": 40,
    "synonyms": 24,
    "antonyms": 24,
    "tags": 18,
    "memo": 30,
    "source_url": 30,
    "created_at": 22,
    "updated_at": 22,
}

HEADER_FILL = PatternFill(start_color="FF22272E", end_color="FF22272E", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFFFF")


def label_to_key(label) -> str:
    """Map an Excel header cell value back to the canonical field key."""
    if not isinstance(label, str):
        return ""
    for key, expected in COLUMN_LABELS.items():
        if expected == label:
            return key
    return label.lower().replace(" ", "_").replace("/", "_")


def render_cell(entry: VocabularyEntry, key: str) -> str:
    if key == "language":
        return entry.language
    if key == "word":
        return entry.word
    if key == "reading":
        return entry.reading or ""
    if key == "part_of_speech":
        return ", ".join(entry.part_of_speech)
    if key == "meanings_summary":
        return entry.meanings_summary or build_meanings_summary(entry)
    if key == "meanings_detail":
        return render_detail(entry.meaning_groups)
    if key == "examples":
        return "\n".join(
            iter_example_plain(entry.examples_flat or _flatten_examples(entry))
        )
    if key == "example_translations":
        return "\n".join(
            iter_example_translation(entry.examples_flat or _flatten_examples(entry))
        )
    if key == "synonyms":
        return ", ".join(entry.synonyms)
    if key == "antonyms":
        return ", ".join(entry.antonyms)
    if key == "tags":
        return ", ".join(entry.tags)
    if key == "memo":
        return entry.memo
    if key == "source_url":
        return entry.source_url or ""
    if key == "created_at":
        return entry.created_at
    if key == "updated_at":
        return entry.updated_at
    return ""


def _flatten_examples(entry: VocabularyEntry) -> list[Example]:
    return collect_examples_flat(entry)


def iter_example_plain(examples: Iterable[Example]) -> list[str]:
    return [ex.source_text_plain for ex in examples if ex.source_text_plain]


def iter_example_translation(examples: Iterable[Example]) -> list[str]:
    return [ex.translation_ko or "" for ex in examples]


def render_detail(groups: list[MeaningGroup]) -> str:
    """Plain-text rendering of the nested meaning structure for Excel."""
    lines: list[str] = []
    for group in groups:
        if group.pos:
            lines.append(group.pos)
        for sense in group.senses:
            head = f"{sense.number}." if sense.number else "-"
            gloss = sense.gloss or ""
            lines.append(f"  {head} {gloss}".rstrip())
            for sub in sense.sub_senses:
                tag = f"{sub.label}." if sub.label else "-"
                lines.append(f"    {tag} {sub.gloss}".rstrip())
                if sub.synonyms:
                    lines.append(f"      = {', '.join(sub.synonyms)}")
    return "\n".join(lines)


def row_to_entry(keys: list[str], row: tuple) -> VocabularyEntry:
    """Reconstruct a VocabularyEntry from an Excel row.

    Populates examples_flat from the `examples` / `example_translations`
    columns so the entry detail dialog has something to render even
    when the SQLite cache is empty (e.g., on a fresh install or after
    `캐시 비우기`). meaning_groups stay empty — the cell text isn't a
    machine-friendly format and the detail dialog already falls back to
    `meanings_summary` line-splits when groups are missing.
    """
    data: dict[str, str] = {}
    for key, value in zip(keys, row):
        if isinstance(value, str):
            data[key] = value
        elif value is None:
            data[key] = ""
        else:
            data[key] = str(value)

    sources = [s for s in data.get("examples", "").split("\n") if s.strip()]
    translations = [s for s in data.get("example_translations", "").split("\n")]
    examples_flat: list[Example] = []
    for idx, src in enumerate(sources):
        examples_flat.append(
            Example(
                source_text=src,
                source_text_plain=src,
                translation_ko=(translations[idx].strip() or None)
                if idx < len(translations)
                else None,
                order=idx,
            )
        )

    return VocabularyEntry(
        language=data.get("language", "en"),  # type: ignore[arg-type]
        word=data.get("word", ""),
        reading=data.get("reading") or None,
        part_of_speech=[s for s in (data.get("part_of_speech", "").split(",")) if s.strip()],
        meanings_summary=data.get("meanings_summary", ""),
        examples_flat=examples_flat,
        memo=data.get("memo", ""),
        synonyms=[s.strip() for s in data.get("synonyms", "").split(",") if s.strip()],
        antonyms=[s.strip() for s in data.get("antonyms", "").split(",") if s.strip()],
        tags=[s.strip() for s in data.get("tags", "").split(",") if s.strip()],
        source_url=data.get("source_url") or None,
        created_at=data.get("created_at") or "",
        updated_at=data.get("updated_at") or "",
    )
