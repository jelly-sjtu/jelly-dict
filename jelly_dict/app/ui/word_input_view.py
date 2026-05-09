from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from app.ui.widgets.language_menu_item import LanguageMenuItem
from app.ui.widgets.wordbook_row import WordbookRow, wordbook_tooltip

WordbookItem = tuple[str, str, str, str]  # word, language, reading, meaning hint


class WordInputView(QtWidgets.QWidget):
    """Command-center style word input with a compact recent list."""

    submitted = QtCore.Signal(str, str)  # word, forced_language ("" = auto)
    clearRecentRequested = QtCore.Signal()
    openWordListRequested = QtCore.Signal(str)
    openSettingsRequested = QtCore.Signal()
    recentEntryRequested = QtCore.Signal(str, str)
    wordbookDeleteRequested = QtCore.Signal(str, object)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._forced_language = ""
        self._list_mode = "recent"
        self._wordbook_items: list[WordbookItem] = []
        self._wordbook_expanded = False
        self._list_height_animation: QtCore.QVariantAnimation | None = None
        self._search_height_animation: QtCore.QVariantAnimation | None = None
        self._language_actions: dict[str, QtWidgets.QWidgetAction | QtCore.QObject] = {}
        # Debounce timer for the wordbook search field — avoids re-rendering
        # the list on every keystroke when the user types fast.
        self._search_debounce = QtCore.QTimer(self)
        self._search_debounce.setSingleShot(True)
        self._search_debounce.setInterval(120)
        self._search_debounce.timeout.connect(self._render_wordbook)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(64, 46, 64, 28)
        layout.setSpacing(14)

        layout.addSpacing(18)

        self.title = QtWidgets.QLabel("jelly dict")
        self.title.setObjectName("heroTitle")
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.title)

        layout.addSpacing(10)

        self.command_panel = QtWidgets.QFrame()
        self.command_panel.setObjectName("commandPanel")
        panel_layout = QtWidgets.QVBoxLayout(self.command_panel)
        panel_layout.setContentsMargins(22, 14, 22, 12)
        panel_layout.setSpacing(6)
        layout.addWidget(self.command_panel, 0, QtCore.Qt.AlignHCenter)

        self.input = QtWidgets.QLineEdit()
        self.input.setObjectName("heroInput")
        self.input.setPlaceholderText("단어를 입력하세요")
        font = self.input.font()
        font.setFamily("Apple SD Gothic Neo")
        font.setPointSize(15)
        self.input.setFont(font)
        self.input.setMinimumHeight(38)
        panel_layout.addWidget(self.input)

        controls = QtWidgets.QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(2)
        panel_layout.addLayout(controls)
        controls.addStretch(1)

        self.lang_button = QtWidgets.QPushButton("자동 감지⌄")
        self.lang_button.setObjectName("languageSelector")
        self.lang_button.setMenu(self._build_language_menu())
        controls.addWidget(self.lang_button)

        self.lookup_btn = QtWidgets.QPushButton("조회")
        self.lookup_btn.setObjectName("primaryButton")
        self.lookup_btn.setDefault(True)
        controls.addWidget(self.lookup_btn)

        self.detected_label = QtWidgets.QLabel("")
        self.detected_label.setObjectName("detectedLabel")
        self.detected_label.setVisible(False)
        panel_layout.addWidget(self.detected_label, 0, QtCore.Qt.AlignRight)

        layout.addSpacing(16)

        recent_panel = QtWidgets.QFrame()
        recent_panel.setObjectName("recentPanel")
        recent_layout = QtWidgets.QVBoxLayout(recent_panel)
        recent_layout.setContentsMargins(20, 18, 20, 18)
        recent_layout.setSpacing(14)
        layout.addWidget(recent_panel, 0, QtCore.Qt.AlignHCenter)

        recent_header = QtWidgets.QHBoxLayout()
        recent_header.setContentsMargins(2, 0, 2, 0)
        recent_header.setSpacing(10)
        recent_layout.addLayout(recent_header)

        self.wordbook_expand_btn = QtWidgets.QPushButton("↙")
        self.wordbook_expand_btn.setObjectName("wordbookExpandButton")
        self.wordbook_expand_btn.setToolTip("단어장 크게 보기")
        self.wordbook_expand_btn.setVisible(False)
        recent_header.addWidget(self.wordbook_expand_btn)

        self.recent_title_btn = QtWidgets.QPushButton("최근 단어⌄")
        self.recent_title_btn.setObjectName("recentTitleButton")
        self.recent_title_btn.setMenu(self._build_word_list_menu())
        recent_header.addWidget(self.recent_title_btn)
        recent_header.addStretch(1)
        self.clear_recent_btn = QtWidgets.QPushButton("목록 지우기")
        self.clear_recent_btn.setObjectName("ghostButton")
        self.clear_recent_btn.setToolTip("Excel/캐시는 유지, 표시만 지움")
        recent_header.addWidget(self.clear_recent_btn)
        self.wordbook_delete_btn = QtWidgets.QPushButton("선택 삭제")
        self.wordbook_delete_btn.setObjectName("wordbookDeleteButton")
        self.wordbook_delete_btn.setVisible(False)
        self.wordbook_delete_btn.setEnabled(False)
        recent_header.addWidget(self.wordbook_delete_btn)

        self.wordbook_search = QtWidgets.QLineEdit()
        self.wordbook_search.setObjectName("wordbookSearch")
        self.wordbook_search.setPlaceholderText("단어 / 뜻 검색...")
        self.wordbook_search.setVisible(False)
        recent_layout.addWidget(self.wordbook_search)

        self.recent_list = QtWidgets.QListWidget()
        self.recent_list.setObjectName("recentList")
        self.recent_list.setFlow(QtWidgets.QListView.TopToBottom)
        self.recent_list.setWrapping(False)
        self.recent_list.setResizeMode(QtWidgets.QListView.Adjust)
        self.recent_list.setMovement(QtWidgets.QListView.Static)
        self.recent_list.setSpacing(7)
        self.recent_list.setUniformItemSizes(True)
        self.recent_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.recent_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.recent_list.setFixedHeight(410)
        recent_layout.addWidget(self.recent_list)

        footer = QtWidgets.QHBoxLayout()
        footer.setSpacing(14)
        footer.setContentsMargins(0, 18, 0, 0)
        layout.addLayout(footer)
        footer.addStretch(1)

        self.status_summary = QtWidgets.QLabel("")
        self.status_summary.setObjectName("statusSummary")
        self.status_summary.setAlignment(QtCore.Qt.AlignCenter)
        self.status_summary.setWordWrap(False)
        self.status_summary.setMinimumWidth(560)
        footer.addWidget(self.status_summary)

        self.settings_btn = QtWidgets.QPushButton("설정")
        self.settings_btn.setObjectName("footerSettingsButton")
        footer.addWidget(self.settings_btn)
        footer.addStretch(1)

        layout.addStretch(1)

        self.input.returnPressed.connect(self._submit)
        self.lookup_btn.clicked.connect(self._submit)
        self.recent_list.itemDoubleClicked.connect(self._open_recent_entry)
        self.recent_list.itemSelectionChanged.connect(self._on_list_selection_changed)
        self.clear_recent_btn.clicked.connect(self.clearRecentRequested.emit)
        self.wordbook_delete_btn.clicked.connect(self._request_wordbook_delete)
        self.wordbook_expand_btn.clicked.connect(self._toggle_wordbook_expanded)
        # Restart the debounce timer on every keystroke; final render
        # happens once the user pauses typing.
        self.wordbook_search.textChanged.connect(
            lambda _text: self._search_debounce.start()
        )
        self.settings_btn.clicked.connect(self.openSettingsRequested.emit)

    def _submit(self) -> None:
        word = self.input.text().strip()
        if not word:
            return
        self.submitted.emit(word, self._forced_language)

    def _build_language_menu(self) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(self)
        menu.setObjectName("languageMenu")
        for label, subtitle, value in [
            ("자동 감지", "입력 문자로 영어/일본어를 판단", ""),
            ("English", "네이버 영어사전으로 조회", "en"),
            ("日本語", "네이버 일본어사전으로 조회", "ja"),
        ]:
            action = QtWidgets.QWidgetAction(menu)
            item = LanguageMenuItem(label, subtitle)
            item.clicked.connect(lambda _=False, v=value: self._set_language(v))
            action.setDefaultWidget(item)
            menu.addAction(action)
            self._language_actions[value] = action
        menu.aboutToShow.connect(self._sync_language_menu)
        return menu

    def _build_word_list_menu(self) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(self)
        menu.setObjectName("languageMenu")
        for label, subtitle, value in [
            ("최근 단어", "최근 조회한 단어 보기", "recent"),
            ("영어 단어장", "저장된 영어 단어 관리", "en"),
            ("일본어 단어장", "저장된 일본어 단어 관리", "ja"),
        ]:
            action = QtWidgets.QWidgetAction(menu)
            item = LanguageMenuItem(label, subtitle)
            item.clicked.connect(lambda _=False, v=value, m=menu: self._open_word_list(v, m))
            action.setDefaultWidget(item)
            menu.addAction(action)
        return menu

    def _open_word_list(self, language: str, menu: QtWidgets.QMenu) -> None:
        menu.close()
        self.openWordListRequested.emit(language)

    def _set_language(self, value: str) -> None:
        self._forced_language = value
        labels = {"": "자동 감지", "en": "English", "ja": "日本語"}
        self.lang_button.setText(f"{labels.get(value, '자동 감지')}⌄")
        menu = self.lang_button.menu()
        if menu is not None:
            menu.close()

    def _sync_language_menu(self) -> None:
        for value, action in self._language_actions.items():
            widget = action.defaultWidget()  # type: ignore[attr-defined]
            if isinstance(widget, LanguageMenuItem):
                widget.set_selected(value == self._forced_language)

    def _open_recent_entry(self, item: QtWidgets.QListWidgetItem) -> None:
        payload = item.data(QtCore.Qt.UserRole)
        if isinstance(payload, tuple) and len(payload) == 2:
            word, language = payload
            self.recentEntryRequested.emit(str(word), str(language))

    def reset_input(self) -> None:
        self.input.clear()
        self.input.setFocus()

    def set_detection_label(self, text: str) -> None:
        self.detected_label.setText(text)
        self.detected_label.setVisible(bool(text))

    def set_recent(self, items: list[tuple[str, str, str]]) -> None:
        """Each item is (word, language, hint). Hint is the first Korean
        meaning shown after an em-dash so the user can verify saves at a
        glance."""
        self._list_mode = "recent"
        self._wordbook_items = []
        self._wordbook_expanded = False
        self.title.setVisible(True)
        self.command_panel.setVisible(True)
        self.recent_title_btn.setText("최근 단어⌄")
        self.wordbook_expand_btn.setVisible(False)
        self.clear_recent_btn.setVisible(True)
        self.wordbook_delete_btn.setVisible(False)
        self.wordbook_delete_btn.setEnabled(False)
        self.wordbook_search.setVisible(False)
        self._search_debounce.stop()
        self.wordbook_search.clear()
        self.wordbook_search.setMaximumHeight(16777215)
        self.recent_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.recent_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.recent_list.setFixedHeight(410)
        self.recent_list.clear()
        for word, language, hint in items[:8]:
            label = f"[{language}] {word}"
            if hint:
                label += f"  —  {hint}"
            display_label = _elide(label, 58)
            qt_item = QtWidgets.QListWidgetItem(label)
            qt_item.setText(display_label)
            qt_item.setData(QtCore.Qt.UserRole, (word, language))
            qt_item.setToolTip(label)
            qt_item.setSizeHint(QtCore.QSize(620, 36))
            self.recent_list.addItem(qt_item)

    def set_wordbook(self, language: str, items: list[WordbookItem]) -> None:
        self._list_mode = language
        self._wordbook_items = list(items)
        title = "일본어 단어장⌄" if language == "ja" else "영어 단어장⌄"
        self.recent_title_btn.setText(title)
        self.title.setVisible(not self._wordbook_expanded)
        self.command_panel.setVisible(not self._wordbook_expanded)
        self.wordbook_expand_btn.setVisible(True)
        self.wordbook_expand_btn.setText("↗" if self._wordbook_expanded else "↙")
        self.clear_recent_btn.setVisible(False)
        self.wordbook_delete_btn.setVisible(True)
        self.wordbook_search.setVisible(not self._wordbook_expanded)
        self.wordbook_search.setMaximumHeight(0 if self._wordbook_expanded else 16777215)
        self.recent_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.recent_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.recent_list.setFixedHeight(650 if self._wordbook_expanded else 410)
        # Mode transition: drop any items from the previous (recent) mode
        # so leftover text labels don't bleed through under the wordbook
        # row widgets we install via setItemWidget.
        self.recent_list.clear()
        self._render_wordbook()

    def _render_wordbook(self) -> None:
        if self._list_mode not in ("en", "ja"):
            return
        needle = self.wordbook_search.text().strip().lower()
        if needle:
            items = [
                item
                for item in self._wordbook_items
                if needle in item[0].lower()
                or needle in item[2].lower()
                or needle in item[3].lower()
            ]
        else:
            items = list(self._wordbook_items)

        # Reuse existing items in place when the count matches: avoids
        # tearing down + rebuilding QWidget instances on every render
        # (matters when filtering a large wordbook). Visual output is
        # identical to the previous "clear + addItem in a loop" path.
        self.recent_list.setUpdatesEnabled(False)
        try:
            self.recent_list.clearSelection()
            current = self.recent_list.count()
            target = len(items)
            for i in range(min(current, target)):
                word, item_language, reading, hint = items[i]
                qt_item = self.recent_list.item(i)
                qt_item.setData(QtCore.Qt.UserRole, (word, item_language))
                qt_item.setToolTip(wordbook_tooltip(item_language, word, reading, hint))
                qt_item.setSizeHint(QtCore.QSize(620, 62))
                self.recent_list.setItemWidget(
                    qt_item, WordbookRow(item_language, word, reading, hint)
                )
            # Append any extra rows.
            for i in range(current, target):
                word, item_language, reading, hint = items[i]
                qt_item = QtWidgets.QListWidgetItem()
                qt_item.setData(QtCore.Qt.UserRole, (word, item_language))
                qt_item.setToolTip(wordbook_tooltip(item_language, word, reading, hint))
                qt_item.setSizeHint(QtCore.QSize(620, 62))
                self.recent_list.addItem(qt_item)
                self.recent_list.setItemWidget(
                    qt_item, WordbookRow(item_language, word, reading, hint)
                )
            # Drop trailing rows from the previous render.
            while self.recent_list.count() > target:
                self.recent_list.takeItem(self.recent_list.count() - 1)
        finally:
            self.recent_list.setUpdatesEnabled(True)
        self._on_list_selection_changed()

    def _toggle_wordbook_expanded(self) -> None:
        if self._list_mode not in ("en", "ja"):
            return
        self._wordbook_expanded = not self._wordbook_expanded
        if self._wordbook_expanded and self.wordbook_search.text():
            self.wordbook_search.clear()
        self.title.setVisible(not self._wordbook_expanded)
        self.command_panel.setVisible(not self._wordbook_expanded)
        self.wordbook_expand_btn.setText("↗" if self._wordbook_expanded else "↙")
        self.wordbook_expand_btn.setToolTip(
            "단어장 줄이기" if self._wordbook_expanded else "단어장 크게 보기"
        )
        self._animate_wordbook_layout()

    def _animate_wordbook_layout(self) -> None:
        start_height = self.recent_list.height()
        end_height = 650 if self._wordbook_expanded else 410
        if self._list_height_animation is not None:
            self._list_height_animation.stop()
        self._list_height_animation = QtCore.QVariantAnimation(self)
        self._list_height_animation.setStartValue(start_height)
        self._list_height_animation.setEndValue(end_height)
        self._list_height_animation.setDuration(220)
        self._list_height_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._list_height_animation.valueChanged.connect(
            lambda value: self.recent_list.setFixedHeight(int(value))
        )
        self._list_height_animation.start()

        if self._search_height_animation is not None:
            self._search_height_animation.stop()
        full_search_height = max(self.wordbook_search.sizeHint().height(), 34)
        if not self._wordbook_expanded:
            self.wordbook_search.setVisible(True)
        self._search_height_animation = QtCore.QVariantAnimation(self)
        self._search_height_animation.setStartValue(
            self.wordbook_search.height() if self.wordbook_search.isVisible() else 0
        )
        self._search_height_animation.setEndValue(0 if self._wordbook_expanded else full_search_height)
        self._search_height_animation.setDuration(180)
        self._search_height_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._search_height_animation.valueChanged.connect(
            lambda value: self.wordbook_search.setMaximumHeight(int(value))
        )
        self._search_height_animation.finished.connect(self._finish_search_animation)
        self._search_height_animation.start()

    def _finish_search_animation(self) -> None:
        if self._wordbook_expanded:
            self.wordbook_search.setVisible(False)
            return
        self.wordbook_search.setMaximumHeight(16777215)

    def _on_list_selection_changed(self) -> None:
        if self._list_mode not in ("en", "ja"):
            return
        count = len(self.recent_list.selectedItems())
        self.wordbook_delete_btn.setEnabled(count > 0)
        self.wordbook_delete_btn.setText(f"선택 삭제 ({count})" if count else "선택 삭제")

    def _request_wordbook_delete(self) -> None:
        if self._list_mode not in ("en", "ja"):
            return
        words: list[str] = []
        for item in self.recent_list.selectedItems():
            payload = item.data(QtCore.Qt.UserRole)
            if isinstance(payload, tuple) and len(payload) == 2:
                words.append(str(payload[0]))
        if words:
            self.wordbookDeleteRequested.emit(self._list_mode, words)

    def set_status_summary(self, text: str) -> None:
        self.status_summary.setText(text)


def _elide(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"

