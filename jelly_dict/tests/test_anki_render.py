from __future__ import annotations

from pathlib import Path

import pytest

from app.anki import apkg_exporter, render, tsv_exporter
from app.core.models import (
    Example,
    MeaningGroup,
    Sense,
    SubSense,
    VocabularyEntry,
    build_meanings_summary,
    collect_examples_flat,
)


def _ja_entry() -> VocabularyEntry:
    entry = VocabularyEntry(
        language="ja",
        word="月日",
        reading="つきひ",
        part_of_speech=["명사"],
        meaning_groups=[
            MeaningGroup(
                pos="명사",
                senses=[
                    Sense(
                        number=1,
                        gloss="월일.",
                        sub_senses=[
                            SubSense(
                                label="a",
                                gloss="시일; 세월.",
                                examples=[
                                    Example(
                                        source_text="<ruby>月<rt>つき</rt></ruby><ruby>日<rt>ひ</rt></ruby>が経つ",
                                        source_text_plain="月日が経つ",
                                        translation_ko="시일이 지나다",
                                    )
                                ],
                                synonyms=["としつき"],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    entry.examples_flat = collect_examples_flat(entry)
    entry.meanings_summary = build_meanings_summary(entry)
    return entry


def test_render_meaning_detail_includes_pos_and_synonym_chip():
    html = render.render_meaning_detail(_ja_entry())
    assert "명사" in html
    assert "시일; 세월." in html
    assert "동의어" in html
    assert "としつき" in html


def test_render_keeps_ruby_html_in_examples():
    html = render.render_meaning_detail(_ja_entry())
    assert "<ruby>" in html


def test_fields_for_entry_has_all_required_fields():
    fields = render.fields_for_entry(_ja_entry())
    for key in render.FIELD_ORDER:
        assert key in fields


def test_tsv_export_writes_file(tmp_path: Path):
    out = tmp_path / "deck.tsv"
    count = tsv_exporter.export_tsv(out, [_ja_entry()])
    assert count == 1
    text = out.read_text(encoding="utf-8-sig")
    assert "#columns:" in text
    assert "月日" in text


def test_apkg_export_writes_file(tmp_path: Path):
    pytest.importorskip("genanki")
    out = tmp_path / "deck.apkg"
    count = apkg_exporter.export_apkg(out, [_ja_entry()], deck_name="Test")
    assert count == 1
    assert out.exists() and out.stat().st_size > 0


def test_apkg_guid_stable_across_runs():
    g1 = apkg_exporter._note_guid("ja", "月日")
    g2 = apkg_exporter._note_guid("ja", "月日")
    assert g1 == g2
    assert apkg_exporter._note_guid("ja", "月日") != apkg_exporter._note_guid("en", "apple")
