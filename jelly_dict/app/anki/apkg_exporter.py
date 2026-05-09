"""APKG (genanki) exporter.

Two stable note types so re-imports update existing cards instead of
creating duplicates:
  - JellyDict::English  (model id MODEL_ID_EN)
  - JellyDict::Japanese (model id MODEL_ID_JA)

Note GUID = SHA1(language|word_key) -> repeated exports update in place.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from app.anki.render import FIELD_ORDER, fields_for_entry, load_template
from app.core.errors import ExportError
from app.core.models import Language, VocabularyEntry, normalize_word_key

# Stable model IDs. Do not change: changing these splits a user's deck.
MODEL_ID_EN = 1_701_524_001
MODEL_ID_JA = 1_701_524_002
DECK_ID_DEFAULT = 1_701_524_100


def export_apkg(
    path: Path,
    entries: Iterable[VocabularyEntry],
    deck_name: str,
) -> int:
    try:
        import genanki
    except ImportError as exc:  # pragma: no cover
        raise ExportError(
            "genanki is not installed. Run `pip install genanki`."
        ) from exc

    front = load_template("card_front.html")
    back = load_template("card_back.html")
    css = load_template("style.css")

    fields = [{"name": name} for name in FIELD_ORDER]
    template = {"name": "Card 1", "qfmt": front, "afmt": back}

    model_en = genanki.Model(
        MODEL_ID_EN,
        "JellyDict::English",
        fields=fields,
        templates=[template],
        css=css,
    )
    model_ja = genanki.Model(
        MODEL_ID_JA,
        "JellyDict::Japanese",
        fields=fields,
        templates=[template],
        css=css,
    )

    deck = genanki.Deck(_deck_id(deck_name), deck_name)

    count = 0
    for entry in entries:
        model = model_en if entry.language == "en" else model_ja
        values = fields_for_entry(entry)
        note = genanki.Note(
            model=model,
            fields=[values.get(name, "") for name in FIELD_ORDER],
            tags=[t.replace(" ", "_") for t in entry.tags if t.strip()],
            guid=_note_guid(entry.language, entry.word),
        )
        deck.add_note(note)
        count += 1

    package = genanki.Package(deck)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        package.write_to_file(str(path))
    except OSError as exc:
        raise ExportError(str(exc)) from exc
    return count


def _note_guid(language: Language, word: str) -> str:
    key = normalize_word_key(word, language)
    return hashlib.sha1(f"{language}|{key}".encode("utf-8")).hexdigest()[:16]


def _deck_id(deck_name: str) -> int:
    digest = hashlib.sha1(deck_name.encode("utf-8")).digest()
    return DECK_ID_DEFAULT ^ int.from_bytes(digest[:4], "big")
