"""Anki TSV / APKG export flow.

Extracted from MainWindow as a small delegate. Behavior is identical
to the previous inline implementation: same file dialog default paths,
same deck name format, same message strings.

Heavy work (genanki APKG generation, Excel scan) runs on a QThread so
the window doesn't freeze on large decks. The user still sees the same
final completion / failure dialogs.
"""
from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from app.services.export_service import ExportService
from app.storage.settings_store import Settings
from app.ui.export_worker import ExportWorker


class ExportController(QtCore.QObject):
    def __init__(
        self,
        parent: QtWidgets.QWidget,
        settings: Settings,
        export_service: ExportService,
    ) -> None:
        super().__init__(parent)
        self._parent = parent
        self._settings = settings
        self._export_service = export_service
        # Holds the active thread so it isn't garbage-collected mid-run.
        self._active_thread: QtCore.QThread | None = None
        self._active_worker: ExportWorker | None = None
        self._busy_dialog: QtWidgets.QProgressDialog | None = None
        self._success_title = ""

    def update_settings(
        self, settings: Settings, export_service: ExportService | None = None
    ) -> None:
        self._settings = settings
        if export_service is not None:
            self._export_service = export_service

    def close(self) -> None:
        if self._active_thread is not None and self._active_thread.isRunning():
            self._active_thread.quit()
            self._active_thread.wait(2000)
        if self._busy_dialog is not None:
            self._busy_dialog.close()

    def is_running(self) -> bool:
        if self._active_thread is None:
            return False
        try:
            return self._active_thread.isRunning()
        except RuntimeError:
            self._clear_active()
            return False

    # ---------- public entry points -----------------------------------

    def export_tsv(self, language: str) -> None:
        default = Path(self._settings.anki_path_for(language)).with_suffix(".tsv")
        path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
            self._parent,
            f"Anki TSV 저장 ({language})",
            str(default),
            "TSV (*.tsv)",
        )
        if not path_str:
            return
        self._run_async(
            kind="tsv",
            output_path=Path(path_str),
            language=language,
            success_title="Anki TSV",
        )

    def export_apkg(self, language: str) -> None:
        default = Path(self._settings.anki_path_for(language))
        path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
            self._parent,
            f"Anki APKG 저장 ({language})",
            str(default),
            "APKG (*.apkg)",
        )
        if not path_str:
            return
        deck_name = f"{self._settings.default_deck_name}::{language.upper()}"
        self._run_async(
            kind="apkg",
            output_path=Path(path_str),
            language=language,
            success_title="Anki APKG",
            deck_name=deck_name,
        )

    # ---------- internal ----------------------------------------------

    def _run_async(
        self,
        *,
        kind: str,
        output_path: Path,
        language: str,
        success_title: str,
        deck_name: str | None = None,
    ) -> None:
        # Show an indeterminate progress dialog so the user sees the app
        # is working. Cancel button does not interrupt the genanki call
        # (the underlying library is synchronous), but the UI returns
        # control as soon as the worker finishes.
        progress = QtWidgets.QProgressDialog(
            f"내보내는 중… ({language})",
            None,  # no cancel — would leave a half-written file
            0, 0,  # range gets switched to (0, total) on first progress emit
            self._parent,
        )
        progress.setWindowTitle(success_title)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        self._success_title = success_title
        self._busy_dialog = progress

        thread = QtCore.QThread(self)
        worker = ExportWorker(
            self._export_service,
            kind,  # type: ignore[arg-type]
            output_path,
            language,
            deck_name,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        if hasattr(worker, "progress"):
            worker.progress.connect(self._on_export_progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_active)

        self._active_thread = thread
        self._active_worker = worker
        thread.start()

    def _on_export_progress(self, current: int, total: int, word: str) -> None:
        if self._busy_dialog is None:
            return
        # Switch from indeterminate to determinate the first time we see
        # a real total. Truncate the displayed word so the dialog doesn't
        # grow horizontally.
        if self._busy_dialog.maximum() != total:
            self._busy_dialog.setRange(0, total)
        self._busy_dialog.setValue(current)
        shown = (word[:18] + "…") if len(word) > 18 else word
        pct = int(current * 100 / total) if total else 0
        self._busy_dialog.setLabelText(
            f"내보내는 중… {current} / {total}  ({pct}%)\n{shown}"
        )

    @QtCore.Slot(int)
    def _on_finished(self, count: int) -> None:
        if self._busy_dialog is not None:
            self._busy_dialog.close()
        QtWidgets.QMessageBox.information(
            self._parent, self._success_title, f"{count}개 카드 내보냄"
        )

    @QtCore.Slot(str)
    def _on_failed(self, message: str) -> None:
        if self._busy_dialog is not None:
            self._busy_dialog.close()
        QtWidgets.QMessageBox.warning(self._parent, "내보내기 실패", message)

    @QtCore.Slot()
    def _clear_active(self) -> None:
        self._active_thread = None
        self._active_worker = None
        self._busy_dialog = None
