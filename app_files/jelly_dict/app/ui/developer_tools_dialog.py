from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from app.core import config


class DeveloperToolsDialog(QtWidgets.QDialog):
    """Small log viewer kept out of the primary user workflow."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("개발자 도구")
        self.resize(820, 560)
        self._log_path = config.log_path()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QtWidgets.QHBoxLayout()
        layout.addLayout(header)
        title = QtWidgets.QLabel("앱 로그")
        title.setObjectName("dialogTitle")
        header.addWidget(title)
        header.addStretch(1)
        path_label = QtWidgets.QLabel(str(self._log_path))
        path_label.setObjectName("mutedLabel")
        path_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        header.addWidget(path_label)

        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        font.setPointSize(12)
        self.log_view.setFont(font)
        layout.addWidget(self.log_view, 1)

        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)
        self.refresh_btn = QtWidgets.QPushButton("새로고침")
        self.copy_btn = QtWidgets.QPushButton("로그 복사")
        self.open_location_btn = QtWidgets.QPushButton("로그 파일 위치 열기")
        self.clear_btn = QtWidgets.QPushButton("로그 비우기")
        close_btn = QtWidgets.QPushButton("닫기")
        buttons.addWidget(self.refresh_btn)
        buttons.addWidget(self.copy_btn)
        buttons.addWidget(self.open_location_btn)
        buttons.addWidget(self.clear_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        self.refresh_btn.clicked.connect(self.refresh)
        self.copy_btn.clicked.connect(self._copy)
        self.open_location_btn.clicked.connect(self._open_location)
        self.clear_btn.clicked.connect(self._clear)
        close_btn.clicked.connect(self.accept)

    @QtCore.Slot()
    def refresh(self) -> None:
        if not self._log_path.exists():
            self.log_view.setPlainText("로그 파일이 아직 없습니다.")
            return
        try:
            text = self._log_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self.log_view.setPlainText(f"로그를 읽을 수 없습니다: {exc}")
            return
        self.log_view.setPlainText(text or "로그가 비어 있습니다.")
        cursor = self.log_view.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.log_view.setTextCursor(cursor)

    def _copy(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self.log_view.toPlainText())

    def _open_location(self) -> None:
        path = self._log_path.parent if self._log_path.parent.exists() else config.runtime_dir()
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))

    def _clear(self) -> None:
        try:
            Path(self._log_path).write_text("", encoding="utf-8")
        except OSError as exc:
            self.log_view.setPlainText(f"로그를 비울 수 없습니다: {exc}")
            return
        self.refresh()
