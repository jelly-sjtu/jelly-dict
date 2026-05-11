"""Background worker for Anki TSV/APKG exports.

Keeping the export off the UI thread avoids freezing the window when
the workbook is large or genanki has to write hundreds of cards.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from PySide6 import QtCore

from app.services.export_service import ExportService

log = logging.getLogger(__name__)


class ExportWorker(QtCore.QObject):
    finished = QtCore.Signal(int)  # written count
    failed = QtCore.Signal(str)
    progress = QtCore.Signal(int, int, str)  # current, total, current_word

    def __init__(
        self,
        service: ExportService,
        kind: Literal["tsv", "apkg"],
        output_path: Path,
        language: str,
        deck_name: str | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._kind = kind
        self._output_path = output_path
        self._language = language
        self._deck_name = deck_name

    @QtCore.Slot()
    def run(self) -> None:
        try:
            if self._kind == "tsv":
                count = self._service.export_tsv(
                    self._output_path, language=self._language
                )
            else:
                count = self._service.export_apkg(
                    self._output_path,
                    deck_name=self._deck_name or "JellyDict",
                    language=self._language,
                    progress_callback=self._emit_progress,
                )
        except Exception as exc:  # pragma: no cover - safety net
            log.exception("export worker crashed")
            self.failed.emit(str(exc))
            return
        self.finished.emit(count)

    def _emit_progress(self, current: int, total: int, word: str) -> None:
        # Qt signal across threads — automatically queued to UI thread.
        self.progress.emit(current, total, word)
