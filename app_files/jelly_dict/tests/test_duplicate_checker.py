from __future__ import annotations

from app.core.duplicate_checker import apply_policy, is_duplicate
from app.core.models import (
    Example,
    MeaningGroup,
    Sense,
    SubSense,
    VocabularyEntry,
    collect_examples_flat,
)


def _make(word: str, language: str = "en", **kwargs) -> VocabularyEntry:
    entry = VocabularyEntry(language=language, word=word, **kwargs)  # type: ignore[arg-type]
    return entry


def test_is_duplicate_uses_normalized_key():
    a = _make(" Apple ")
    b = _make("apple")
    assert is_duplicate(a, b)


def test_is_duplicate_returns_false_for_different_languages():
    assert not is_duplicate(_make("apple", "en"), _make("apple", "ja"))


def test_keep_existing_returns_none():
    existing = _make("apple", memo="old")
    new = _make("apple", memo="new")
    assert apply_policy(existing, new, "keep_existing") is None


def test_update_existing_preserves_id_and_created_at():
    existing = _make("apple", memo="old")
    existing_id = existing.id
    existing_created = existing.created_at

    new = _make("apple", memo="new")
    result = apply_policy(existing, new, "update_existing")

    assert result is not None
    assert result.id == existing_id
    assert result.created_at == existing_created
    assert result.memo == "new"


def test_merge_unions_lists_and_appends_memo():
    existing = _make(
        "apple",
        memo="old",
        synonyms=["fruit"],
        tags=["food"],
    )
    existing.examples_flat = [
        Example(source_text_plain="I ate an apple.", translation_ko="사과")
    ]

    new = _make(
        "apple",
        memo="extra",
        synonyms=["pomme"],
        tags=["food", "snack"],
    )
    new.meaning_groups = [
        MeaningGroup(
            pos="noun",
            senses=[
                Sense(
                    number=1,
                    sub_senses=[
                        SubSense(
                            examples=[
                                Example(
                                    source_text_plain="An apple a day.",
                                    translation_ko="하루 사과",
                                )
                            ]
                        )
                    ],
                )
            ],
        )
    ]
    new.examples_flat = collect_examples_flat(new)

    merged = apply_policy(existing, new, "merge_examples_and_memo")

    assert merged is not None
    assert "fruit" in merged.synonyms and "pomme" in merged.synonyms
    assert merged.tags == ["food", "snack"]
    assert "old" in merged.memo and "extra" in merged.memo
    assert any("An apple a day" in ex.source_text_plain for ex in merged.examples_flat)


def test_merge_does_not_duplicate_examples():
    existing = _make("apple")
    existing.examples_flat = [Example(source_text_plain="x", translation_ko="y")]
    new = _make("apple")
    new.examples_flat = [Example(source_text_plain="x", translation_ko="y")]
    merged = apply_policy(existing, new, "merge_examples_and_memo")
    assert merged is not None
    assert len(merged.examples_flat) == 1
