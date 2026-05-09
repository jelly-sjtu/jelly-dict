from __future__ import annotations

from app.core.models import (
    Example,
    MeaningGroup,
    Sense,
    SubSense,
    VocabularyEntry,
    build_meanings_summary,
    collect_examples_flat,
    normalize_word_key,
)


def _sample_ja() -> VocabularyEntry:
    return VocabularyEntry(
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
                                        source_text="月日が経つ",
                                        source_text_plain="月日が経つ",
                                        translation_ko="시일이 지나다",
                                    )
                                ],
                                synonyms=["としつき"],
                            ),
                            SubSense(label="b", gloss="달과 날; 날짜."),
                        ],
                    ),
                    Sense(number=2, gloss="시일."),
                    Sense(number=3, gloss="달과 날."),
                ],
            )
        ],
    )


def test_word_key_english_lowercases():
    assert normalize_word_key(" Apple ", "en") == "apple"


def test_word_key_japanese_nfkc():
    assert normalize_word_key("ｶﾒﾗ", "ja") == "カメラ"


def test_meanings_summary_uses_sense_gloss():
    entry = _sample_ja()
    summary = build_meanings_summary(entry)
    assert summary == "[명사] 1. 월일 2. 시일 3. 달과 날"


def test_meanings_summary_falls_back_to_subsense():
    entry = VocabularyEntry(
        language="ja",
        word="x",
        meaning_groups=[
            MeaningGroup(
                pos="명사",
                senses=[
                    Sense(number=1, gloss="", sub_senses=[SubSense(gloss="대안 뜻; 부가")]),
                ],
            )
        ],
    )
    assert build_meanings_summary(entry) == "[명사] 1. 대안 뜻"


def test_meanings_summary_empty_when_no_groups():
    entry = VocabularyEntry(language="en", word="apple")
    assert build_meanings_summary(entry) == ""


def test_collect_examples_flat_orders_examples():
    entry = _sample_ja()
    flat = collect_examples_flat(entry)
    assert len(flat) == 1
    assert flat[0].order == 0
    assert flat[0].source_text == "月日が経つ"


def test_to_json_round_trip():
    original = _sample_ja()
    payload = original.to_json()
    restored = VocabularyEntry.from_json(payload)
    assert restored.word == original.word
    assert restored.language == original.language
    assert restored.meaning_groups[0].senses[0].sub_senses[0].synonyms == ["としつき"]
    assert (
        restored.meaning_groups[0].senses[0].sub_senses[0].examples[0].source_text
        == "月日が経つ"
    )


def test_word_key_method_matches_helper():
    entry = VocabularyEntry(language="en", word=" Hello ")
    assert entry.word_key() == "hello"
