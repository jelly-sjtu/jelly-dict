"""Compact row widget used inside the wordbook list.

Extracted from `word_input_view.py` to keep that file focused on the
input flow. The widget tree, object names, and styling are byte-for-byte
identical to the original — no UI/UX change.
"""
from __future__ import annotations

from PySide6 import QtWidgets


class WordbookRow(QtWidgets.QFrame):
    def __init__(
        self,
        language: str,
        word: str,
        reading: str,
        hint: str,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("wordbookRow")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(3)

        top = QtWidgets.QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        layout.addLayout(top)

        word_label = QtWidgets.QLabel(word)
        word_label.setObjectName("wordbookWord")
        word_label.setToolTip(word)
        word_label.setMinimumWidth(0)
        word_label.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        top.addWidget(word_label, 0)

        if language == "ja":
            reading_label = QtWidgets.QLabel(reading if reading else "")
            reading_label.setObjectName("wordbookReading")
            reading_label.setToolTip(reading)
            reading_label.setMinimumWidth(0)
            reading_label.setSizePolicy(
                QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
            )
            top.addWidget(reading_label, 0)
        top.addStretch(1)

        meaning_label = QtWidgets.QLabel(hint)
        meaning_label.setObjectName("wordbookMeaning")
        meaning_label.setToolTip(hint)
        meaning_label.setMinimumWidth(0)
        meaning_label.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(meaning_label)


def wordbook_tooltip(language: str, word: str, reading: str, hint: str) -> str:
    if language == "ja" and reading:
        return f"{word}\n{reading}\n{hint}".strip()
    return f"{word}\n{hint}".strip()
