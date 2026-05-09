from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.core.models import VocabularyEntry, build_meanings_summary, collect_examples_flat


class EntryDetailDialog(QtWidgets.QDialog):
    def __init__(self, entry: VocabularyEntry, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._entry = entry
        self.setWindowTitle(_primary_form(entry.word) or "단어 상세")
        self.resize(560, 640)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 18)
        layout.setSpacing(16)

        header = QtWidgets.QHBoxLayout()
        layout.addLayout(header)
        title = QtWidgets.QLabel(_primary_form(self._entry.word))
        title.setObjectName("entryDetailTitle")
        title.setWordWrap(True)
        header.addWidget(title, 1)
        close_btn = QtWidgets.QPushButton("×")
        close_btn.setObjectName("entryDetailClose")
        close_btn.clicked.connect(self.accept)
        header.addWidget(close_btn)

        reading = _primary_form(self._entry.reading or "")
        if reading:
            reading_label = QtWidgets.QLabel(f"[{reading}]")
            reading_label.setObjectName("entryDetailReading")
            reading_label.setWordWrap(True)
            layout.addWidget(reading_label)

        first_gloss = _first_gloss(self._entry)
        if first_gloss:
            summary_label = QtWidgets.QLabel(first_gloss)
            summary_label.setObjectName("entryDetailSummary")
            summary_label.setWordWrap(True)
            layout.addWidget(summary_label)

        meta = []
        if self._entry.part_of_speech:
            meta.append(", ".join(self._entry.part_of_speech))
        if self._entry.source_provider:
            meta.append(_provider_label(self._entry.source_provider))
        if meta:
            meta_label = QtWidgets.QLabel(" · ".join(meta))
            meta_label.setObjectName("entryDetailMeta")
            layout.addWidget(meta_label)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("entryDetailScroll")
        body = QtWidgets.QWidget()
        body_layout = QtWidgets.QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(14)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        self._add_meanings(body_layout)
        self._add_examples(body_layout)
        self._add_word_list(body_layout, "동의어", self._entry.synonyms)
        self._add_word_list(body_layout, "반의어", self._entry.antonyms)
        body_layout.addStretch(1)

    def _add_meanings(self, layout: QtWidgets.QVBoxLayout) -> None:
        if self._entry.meaning_groups:
            for group in self._entry.meaning_groups:
                if group.pos:
                    label = QtWidgets.QLabel(group.pos)
                    label.setObjectName("entryDetailSection")
                    layout.addWidget(label)
                for sense in group.senses:
                    text = sense.gloss.strip()
                    if not text and sense.sub_senses:
                        text = sense.sub_senses[0].gloss.strip()
                    if not text:
                        continue
                    row = QtWidgets.QLabel(f"{sense.number or ''}. {text}".strip())
                    row.setObjectName("entryDetailRow")
                    row.setWordWrap(True)
                    layout.addWidget(row)
            return

        # Fallback: no nested meaning_groups (entry came from Excel-only
        # row). Split the summary string into individual sense rows so
        # multi-sense words read top-to-bottom instead of as one wall.
        for index, gloss in enumerate(_split_summary_senses(self._entry.meanings_summary), start=1):
            row = QtWidgets.QLabel(f"{index}. {gloss}")
            row.setObjectName("entryDetailRow")
            row.setWordWrap(True)
            layout.addWidget(row)

    def _add_examples(self, layout: QtWidgets.QVBoxLayout) -> None:
        examples = self._entry.examples_flat or collect_examples_flat(self._entry)
        if not examples:
            return
        label = QtWidgets.QLabel("예문")
        label.setObjectName("entryDetailSection")
        layout.addWidget(label)
        for ex in examples[:5]:
            text = ex.source_text_plain or ex.source_text
            if ex.translation_ko:
                text += f"\n{ex.translation_ko}"
            row = QtWidgets.QLabel(text)
            row.setObjectName("entryDetailRow")
            row.setWordWrap(True)
            layout.addWidget(row)

    def _add_word_list(self, layout: QtWidgets.QVBoxLayout, title: str, words: list[str]) -> None:
        if not words:
            return
        label = QtWidgets.QLabel(title)
        label.setObjectName("entryDetailSection")
        layout.addWidget(label)
        row = QtWidgets.QLabel(", ".join(words[:12]))
        row.setObjectName("entryDetailRow")
        row.setWordWrap(True)
        layout.addWidget(row)


def _provider_label(provider: str) -> str:
    return {
        "naver_en": "네이버 영어사전",
        "naver_ja": "네이버 일본어사전",
        "manual": "직접 입력",
    }.get(provider, provider)


def _primary_form(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    for sep in ("·", "・", "/", "\\"):
        if sep in text:
            return text.split(sep, 1)[0].strip()
    return text


def _split_summary_senses(summary: str) -> list[str]:
    """Split a meanings_summary string back into individual sense glosses.

    Input formats we tolerate:
      "[Noun] 1. apple 2. computer brand"
      "1. 비관적인"
      "[명사] 1. 월일 2. 시일 3. 달과 날"
    Returns: ["apple", "computer brand"] / ["비관적인"] / ["월일", "시일", "달과 날"].
    """
    import re

    if not summary:
        return []
    # Drop leading "[POS] " if present.
    body = re.sub(r"^\[[^\]]+\]\s*", "", summary).strip()
    if not body:
        return []
    # Split on " <digits>. " — keep the text after each number.
    parts = re.split(r"\s*\d+\s*\.\s*", body)
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned or [body]


def _first_gloss(entry: VocabularyEntry) -> str:
    for group in entry.meaning_groups:
        for sense in group.senses:
            if sense.gloss:
                return sense.gloss.strip()
            for sub in sense.sub_senses:
                if sub.gloss:
                    return sub.gloss.strip()
    summary = entry.meanings_summary or build_meanings_summary(entry)
    if not summary:
        return ""
    senses = _split_summary_senses(summary)
    if senses:
        # Show only the first sense in the header; the body section
        # below renders every sense on its own row for multi-meaning
        # entries so the user can scan them line-by-line.
        return senses[0]
    return summary
