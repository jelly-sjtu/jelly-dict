from __future__ import annotations

import logging
import time
from pathlib import Path

from PySide6 import QtCore

from app.ocr.base import OcrProvider

log = logging.getLogger(__name__)


class OcrWorker(QtCore.QObject):
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, provider: OcrProvider, image_path: Path) -> None:
        super().__init__()
        self._provider = provider
        self._image_path = image_path

    @QtCore.Slot()
    def run(self) -> None:
        started = time.perf_counter()
        try:
            result = self._provider.extract(self._image_path)
            log.info(
                "ocr finished in %.2fs: path=%s tokens=%d",
                time.perf_counter() - started,
                self._image_path,
                len(result.tokens),
            )
            self.finished.emit(result)
        except Exception as exc:
            log.exception("ocr worker failed")
            self.failed.emit(str(exc))
