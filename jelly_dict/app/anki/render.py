"""Renders the nested meaning structure into the HTML used by Anki cards."""
from __future__ import annotations

from html import escape
from pathlib import Path

from app.core.models import (
    Example,
    MeaningGroup,
    Sense,
    SubSense,
    VocabularyEntry,
    build_meanings_summary,
)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def load_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")


def render_meaning_detail(entry: VocabularyEntry) -> str:
    """Render meaning_groups into the structured HTML the Anki card expects."""
    parts: list[str] = []
    for group in entry.meaning_groups:
        parts.append('<div class="meaning-group">')
        if group.pos:
            parts.append(f'<div class="pos">{escape(group.pos)}</div>')
        for sense in group.senses:
            parts.append(_render_sense(sense))
        parts.append("</div>")
    return "".join(parts)


def _render_sense(sense: Sense) -> str:
    out: list[str] = ['<div class="sense">']
    label = f"{sense.number}." if sense.number else ""
    if label or sense.gloss:
        out.append(
            f'<div><span class="sense-label">{escape(label)}</span> '
            f'{escape(sense.gloss)}</div>'
        )
    for sub in sense.sub_senses:
        out.append(_render_sub_sense(sub))
    out.append("</div>")
    return "".join(out)


def _render_sub_sense(sub: SubSense) -> str:
    out: list[str] = ['<div class="sub-sense">']
    label = f"{sub.label}." if sub.label else ""
    out.append(
        f'<div><span class="sub-label">{escape(label)}</span> '
        f'{escape(sub.gloss)}</div>'
    )
    if sub.examples:
        out.append('<div class="examples">')
        for ex in sub.examples:
            out.append(_render_example(ex))
        out.append("</div>")
    if sub.synonyms:
        out.append('<div class="synonyms">')
        out.append('<span class="chip-label">동의어</span>')
        for s in sub.synonyms:
            out.append(f'<span class="chip">{escape(s)}</span>')
        out.append("</div>")
    if sub.antonyms:
        out.append('<div class="synonyms">')
        out.append('<span class="chip-label">반의어</span>')
        for s in sub.antonyms:
            out.append(f'<span class="chip">{escape(s)}</span>')
        out.append("</div>")
    out.append("</div>")
    return "".join(out)


def _render_example(ex: Example) -> str:
    # source_text may already contain <ruby>; trust it. Fall back to plain.
    source = ex.source_text or escape(ex.source_text_plain)
    parts = [
        '<div class="example">',
        f'<span class="example-source">{source}</span>',
    ]
    if ex.translation_ko:
        parts.append(
            f'<span class="example-trans">{escape(ex.translation_ko)}</span>'
        )
    parts.append("</div>")
    return "".join(parts)


def render_examples_html(entry: VocabularyEntry) -> str:
    parts: list[str] = []
    for ex in entry.examples_flat:
        parts.append(_render_example(ex))
    return "".join(parts)


def render_translations_html(entry: VocabularyEntry) -> str:
    return "<br>".join(
        escape(ex.translation_ko or "") for ex in entry.examples_flat
    )


def fields_for_entry(entry: VocabularyEntry) -> dict[str, str]:
    """Return the dict of Anki note fields for an entry."""
    summary = entry.meanings_summary or build_meanings_summary(entry)
    return {
        "Word": entry.word,
        "Reading": entry.reading or "",
        "Language": "EN" if entry.language == "en" else "JA",
        "PartOfSpeech": ", ".join(entry.part_of_speech),
        "MeaningSummary": escape(summary),
        "MeaningDetail": render_meaning_detail(entry),
        "Examples": render_examples_html(entry),
        "ExampleTranslations": render_translations_html(entry),
        "Synonyms": ", ".join(escape(s) for s in entry.synonyms),
        "Antonyms": ", ".join(escape(s) for s in entry.antonyms),
        "Memo": escape(entry.memo or "").replace("\n", "<br>"),
        "SourceURL": entry.source_url or "",
    }


FIELD_ORDER: tuple[str, ...] = (
    "Word",
    "Reading",
    "Language",
    "PartOfSpeech",
    "MeaningSummary",
    "MeaningDetail",
    "Examples",
    "ExampleTranslations",
    "Synonyms",
    "Antonyms",
    "Memo",
    "SourceURL",
)
