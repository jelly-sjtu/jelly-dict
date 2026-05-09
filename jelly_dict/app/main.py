from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from app.core import config


def _setup_logging() -> None:
    log_path: Path = config.log_path()
    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    root.addHandler(stream)


def main() -> int:
    _setup_logging()
    # Touch runtime dir / settings / Excel target so the app is ready.
    config.runtime_dir()
    from app.storage.settings_store import SettingsStore

    settings = SettingsStore().load()
    excel_dir = Path(settings.default_excel_dir)
    excel_dir.mkdir(parents=True, exist_ok=True)

    # Defer Qt import so unit tests / CLI use don't need a display.
    from PySide6 import QtWidgets

    from app.ui.main_window import MainWindow

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
