from __future__ import annotations

import pytest

from app.core.language_detector import detect_language


@pytest.mark.parametrize(
    "text",
    ["apple", "Take", "beautiful", "run into", "give up", "BANANA"],
)
def test_english_words(text):
    assert detect_language(text) == "en"


@pytest.mark.parametrize(
    "text",
    ["つきひ", "カメラ", "食べる", "ありがとう", "アップル"],
)
def test_japanese_with_kana(text):
    assert detect_language(text) == "ja"


@pytest.mark.parametrize(
    "text",
    ["月日", "勉強", "時間", "学校"],
)
def test_kanji_only_treated_as_japanese(text):
    assert detect_language(text) == "ja"


def test_kanji_plus_latin_is_ambiguous():
    assert detect_language("月日 abc") == "ambiguous"


def test_kana_plus_latin_is_ambiguous():
    assert detect_language("カメラ test") == "ambiguous"


@pytest.mark.parametrize("text", ["사과", "안녕", "달과 날", " "])
def test_unsupported_inputs(text):
    assert detect_language(text) == "unsupported"


def test_empty_input():
    assert detect_language("") == "unsupported"
    assert detect_language(None) == "unsupported"
