from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtWidgets

from app.storage.settings_store import Settings, SettingsStore


class SettingsDialog(QtWidgets.QDialog):
    settingsChanged = QtCore.Signal(Settings)

    def __init__(self, store: SettingsStore, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self.setWindowTitle("설정")
        self.resize(860, 560)
        self.setMinimumWidth(780)
        self._build_ui()
        self._load(store.load())

    def _build_ui(self) -> None:
        layout = QtWidgets.QFormLayout(self)
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)

        self.excel_dir = _PathPicker(mode="dir")
        self.excel_en = _PathPicker(mode="file_save", file_filter="Excel (*.xlsx)")
        self.excel_ja = _PathPicker(mode="file_save", file_filter="Excel (*.xlsx)")
        self.anki_dir = _PathPicker(mode="dir")
        self.anki_en = _PathPicker(mode="file_save", file_filter="APKG (*.apkg)")
        self.anki_ja = _PathPicker(mode="file_save", file_filter="APKG (*.apkg)")
        self.delay = QtWidgets.QDoubleSpinBox()
        # Hard floor 0.3s — see _RateLimiter.HARD_FLOOR_SECONDS. Going
        # faster looks like a bot to Naver and risks getting the IP
        # blocked, so we don't expose anything lower in the UI.
        self.delay.setRange(0.3, 60.0)
        self.delay.setSingleStep(0.1)
        self.delay.setDecimals(2)
        self.delay.setSuffix(" s")
        self.delay.setToolTip(
            "요청 간격. 너무 짧으면 네이버에서 차단될 수 있습니다 (최소 0.3초)."
        )
        self.cache_check = QtWidgets.QCheckBox("캐시 사용")
        self.preview_check = QtWidgets.QCheckBox("저장 전 미리보기 화면 표시")
        self.dup_combo = QtWidgets.QComboBox()
        for value, label in [
            ("ask", "묻기 (다이얼로그)"),
            ("update_existing", "덮어쓰기"),
            ("merge_examples_and_memo", "병합"),
            ("keep_existing", "기존 유지"),
            ("add_as_new", "새 항목으로 추가"),
        ]:
            self.dup_combo.addItem(label, value)
        self.deck_name = QtWidgets.QLineEdit()
        self.provider_combo = QtWidgets.QComboBox()
        for value, label in [
            ("naver_crawler", "네이버 사전"),
        ]:
            self.provider_combo.addItem(label, value)

        # AnkiConnect block
        self.ankiconnect_check = QtWidgets.QCheckBox("AnkiConnect 사용 (실시간 Anki 동기화)")
        self.ankiconnect_check.setToolTip(
            "Anki 데스크톱에 AnkiConnect 애드온이 설치돼 있어야 합니다.\n"
            "활성화 시 단어 삭제가 Anki에도 즉시 반영됩니다."
        )
        self.ankiconnect_url = QtWidgets.QLineEdit()
        self.ankiconnect_url.setPlaceholderText("http://127.0.0.1:8765")
        self.ankiconnect_test_btn = QtWidgets.QPushButton("연결 테스트")
        self.ankiconnect_status = QtWidgets.QLabel("")
        self.ankiconnect_status.setStyleSheet("color: #888;")
        url_row = QtWidgets.QWidget()
        url_layout = QtWidgets.QHBoxLayout(url_row)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.addWidget(self.ankiconnect_url, 1)
        url_layout.addWidget(self.ankiconnect_test_btn)
        self.ankiconnect_test_btn.clicked.connect(self._test_ankiconnect)

        layout.addRow("기본 Excel 폴더", self.excel_dir)
        layout.addRow("Excel 파일 (영어)", self.excel_en)
        layout.addRow("Excel 파일 (일본어)", self.excel_ja)
        layout.addRow("Anki 폴더", self.anki_dir)
        layout.addRow("Anki 파일 (영어)", self.anki_en)
        layout.addRow("Anki 파일 (일본어)", self.anki_ja)
        layout.addRow("요청 간격", self.delay)
        layout.addRow("", self.cache_check)
        layout.addRow("", self.preview_check)
        layout.addRow("중복 처리", self.dup_combo)
        layout.addRow("Anki 덱 이름", self.deck_name)
        layout.addRow("사전 소스", self.provider_combo)
        layout.addRow("", self.ankiconnect_check)
        layout.addRow("AnkiConnect URL", url_row)
        layout.addRow("", self.ankiconnect_status)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _load(self, settings: Settings) -> None:
        self.excel_dir.set_path(settings.default_excel_dir)
        self.excel_en.set_path(settings.excel_path_en or settings.excel_path_for("en"))
        self.excel_ja.set_path(settings.excel_path_ja or settings.excel_path_for("ja"))
        self.anki_dir.set_path(settings.default_anki_export_dir)
        self.anki_en.set_path(settings.anki_path_en or settings.anki_path_for("en"))
        self.anki_ja.set_path(settings.anki_path_ja or settings.anki_path_for("ja"))
        self.delay.setValue(settings.request_delay_seconds)
        self.cache_check.setChecked(settings.cache_enabled)
        self.preview_check.setChecked(settings.show_preview)
        idx = self.dup_combo.findData(settings.duplicate_policy)
        if idx >= 0:
            self.dup_combo.setCurrentIndex(idx)
        self.deck_name.setText(settings.default_deck_name)
        idx = self.provider_combo.findData(settings.provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.ankiconnect_check.setChecked(settings.ankiconnect_enabled)
        self.ankiconnect_url.setText(settings.ankiconnect_url)

    def _save(self) -> None:
        updated = self._store.update(
            default_excel_dir=self.excel_dir.path() or "",
            excel_path_en=self.excel_en.path() or "",
            excel_path_ja=self.excel_ja.path() or "",
            default_anki_export_dir=self.anki_dir.path() or "",
            anki_path_en=self.anki_en.path() or "",
            anki_path_ja=self.anki_ja.path() or "",
            request_delay_seconds=float(self.delay.value()),
            cache_enabled=self.cache_check.isChecked(),
            show_preview=self.preview_check.isChecked(),
            duplicate_policy=self.dup_combo.currentData(),
            default_deck_name=self.deck_name.text().strip() or "JellyDict",
            provider=self.provider_combo.currentData(),
            ankiconnect_enabled=self.ankiconnect_check.isChecked(),
            ankiconnect_url=self.ankiconnect_url.text().strip() or "http://127.0.0.1:8765",
        )
        self.settingsChanged.emit(updated)
        self.accept()

    def _test_ankiconnect(self) -> None:
        from app.anki.ankiconnect_client import AnkiConnectClient, AnkiConnectError

        url = self.ankiconnect_url.text().strip() or "http://127.0.0.1:8765"
        client = AnkiConnectClient(url)
        try:
            ok = client.is_available()
        except AnkiConnectError as exc:
            self.ankiconnect_status.setStyleSheet("color: #d33;")
            self.ankiconnect_status.setText(f"연결 실패: {exc}")
            return
        if ok:
            self.ankiconnect_status.setStyleSheet("color: #2a8;")
            self.ankiconnect_status.setText("✓ 연결됨")
        else:
            self.ankiconnect_status.setStyleSheet("color: #d33;")
            self.ankiconnect_status.setText("응답 없음")


class _PathPicker(QtWidgets.QWidget):
    def __init__(self, mode: str = "dir", file_filter: str = "", parent=None) -> None:
        """mode: 'dir' | 'file_save' | 'file_open'"""
        super().__init__(parent)
        self._mode = mode
        self._filter = file_filter
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.line = QtWidgets.QLineEdit()
        self.line.setMinimumWidth(520)
        self.button = QtWidgets.QPushButton("선택…")
        self.button.setMaximumWidth(72)
        layout.addWidget(self.line, 1)
        layout.addWidget(self.button)
        self.button.clicked.connect(self._pick)

    def _pick(self) -> None:
        current = self.line.text()
        if self._mode == "dir":
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "폴더 선택", current)
        elif self._mode == "file_open":
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "기존 파일 선택", current, self._filter
            )
        else:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "저장할 파일 선택 / 새로 만들기", current, self._filter
            )
        if path:
            self.line.setText(path)

    def path(self) -> str:
        return self.line.text().strip()

    def set_path(self, path: str) -> None:
        self.line.setText(path or "")
