from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.core.models import (
    Example,
    MeaningGroup,
    Sense,
    SubSense,
    VocabularyEntry,
    build_meanings_summary,
    collect_examples_flat,
)


class PreviewEditorView(QtWidgets.QWidget):
    """Optional preview/edit screen — toggled by settings.show_preview."""

    saveRequested = QtCore.Signal(VocabularyEntry)
    cancelled = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._entry: VocabularyEntry | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.word_edit = QtWidgets.QLineEdit()
        self.reading_edit = QtWidgets.QLineEdit()
        self.pos_edit = QtWidgets.QLineEdit()
        self.summary_edit = QtWidgets.QLineEdit()
        self.synonyms_edit = QtWidgets.QLineEdit()
        self.antonyms_edit = QtWidgets.QLineEdit()
        self.tags_edit = QtWidgets.QLineEdit()
        self.memo_edit = QtWidgets.QPlainTextEdit()
        self.memo_edit.setFixedHeight(80)
        self.examples_edit = QtWidgets.QPlainTextEdit()
        self.translations_edit = QtWidgets.QPlainTextEdit()
        self.source_label = QtWidgets.QLabel("-")
        self.source_label.setOpenExternalLinks(True)

        form.addRow("단어", self.word_edit)
        form.addRow("읽기/발음", self.reading_edit)
        form.addRow("품사 (콤마구분)", self.pos_edit)
        form.addRow("뜻 요약", self.summary_edit)
        form.addRow("예문 (줄바꿈)", self.examples_edit)
        form.addRow("예문 해석 (줄바꿈)", self.translations_edit)
        form.addRow("동의어", self.synonyms_edit)
        form.addRow("반의어", self.antonyms_edit)
        form.addRow("태그", self.tags_edit)
        form.addRow("메모", self.memo_edit)
        form.addRow("출처", self.source_label)

        button_row = QtWidgets.QHBoxLayout()
        layout.addLayout(button_row)
        button_row.addStretch(1)
        self.cancel_button = QtWidgets.QPushButton("취소")
        self.save_button = QtWidgets.QPushButton("저장")
        self.save_button.setDefault(True)
        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.save_button)

        self.cancel_button.clicked.connect(self.cancelled.emit)
        self.save_button.clicked.connect(self._emit_save)

    def set_entry(self, entry: VocabularyEntry) -> None:
        self._entry = entry
        self.word_edit.setText(entry.word)
        self.reading_edit.setText(entry.reading or "")
        self.pos_edit.setText(", ".join(entry.part_of_speech))
        self.summary_edit.setText(entry.meanings_summary or build_meanings_summary(entry))
        self.summary_edit.setCursorPosition(0)
        self.summary_edit.setToolTip(self.summary_edit.text())
        self.synonyms_edit.setText(", ".join(entry.synonyms))
        self.antonyms_edit.setText(", ".join(entry.antonyms))
        self.tags_edit.setText(", ".join(entry.tags))
        self.memo_edit.setPlainText(entry.memo or "")
        flat = entry.examples_flat or collect_examples_flat(entry)
        self.examples_edit.setPlainText("\n".join(ex.source_text_plain for ex in flat))
        self.translations_edit.setPlainText("\n".join(ex.translation_ko or "" for ex in flat))
        if entry.source_url:
            self.source_label.setText(f'<a href="{entry.source_url}">{entry.source_url}</a>')
        else:
            self.source_label.setText("-")

    def _emit_save(self) -> None:
        if self._entry is None:
            return
        entry = VocabularyEntry.from_dict(self._entry.to_dict())
        entry.word = self.word_edit.text().strip()
        entry.reading = self.reading_edit.text().strip() or None
        entry.part_of_speech = _split_csv(self.pos_edit.text())
        entry.meanings_summary = self.summary_edit.text().strip()
        entry.synonyms = _split_csv(self.synonyms_edit.text())
        entry.antonyms = _split_csv(self.antonyms_edit.text())
        entry.tags = _split_csv(self.tags_edit.text())
        entry.memo = self.memo_edit.toPlainText().strip()

        sources = [s for s in self.examples_edit.toPlainText().split("\n") if s]
        translations = [s for s in self.translations_edit.toPlainText().split("\n")]
        new_examples: list[Example] = []
        for idx, src in enumerate(sources):
            new_examples.append(
                Example(
                    source_text=src,
                    source_text_plain=src,
                    translation_ko=translations[idx] if idx < len(translations) else None,
                    order=idx,
                )
            )
        entry.examples_flat = new_examples
        # Replace nested structure with edited summary + flat examples so
        # downstream consumers stay consistent.
        if not entry.meaning_groups:
            entry.meaning_groups = [
                MeaningGroup(
                    pos=entry.part_of_speech[0] if entry.part_of_speech else "",
                    senses=[
                        Sense(
                            number=1,
                            gloss=entry.meanings_summary,
                            sub_senses=[SubSense(examples=new_examples)],
                        )
                    ],
                )
            ]
        entry.touch()
        self.saveRequested.emit(entry)


def _split_csv(text: str) -> list[str]:
    return [p.strip() for p in (text or "").split(",") if p.strip()]
