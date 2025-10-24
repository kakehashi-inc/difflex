"""History dialog for viewing comparison history."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Signal

from ..utils.settings import Settings


class HistoryDialog(QDialog):
    """Dialog for viewing comparison history."""

    compare_requested = Signal(list, bool)  # paths, is_directory

    def __init__(self, parent=None):
        """Initialize history dialog."""
        super().__init__(parent)
        self.setWindowTitle("比較履歴")
        self.setMinimumSize(700, 400)
        self.settings = Settings()
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["種類", "パス1", "パス2", "パス3"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        rerun_btn = QPushButton("再実行")
        rerun_btn.clicked.connect(self._rerun_comparison)
        button_layout.addWidget(rerun_btn)

        clear_btn = QPushButton("履歴をクリア")
        clear_btn.clicked.connect(self._clear_history)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _load_history(self):
        """Load history from settings."""
        history = self.settings.get_comparison_history()

        self.table.setRowCount(len(history))

        for row, item in enumerate(history):
            is_dir = item.get("is_directory", False)
            paths = item.get("paths", [])

            # Type
            type_item = QTableWidgetItem("ディレクトリ" if is_dir else "ファイル")
            self.table.setItem(row, 0, type_item)

            # Paths
            for i in range(3):
                path = paths[i] if i < len(paths) else ""
                self.table.setItem(row, 1 + i, QTableWidgetItem(path))

    def _on_row_double_clicked(self, index):
        """Handle row double click."""
        self._rerun_comparison()

    def _rerun_comparison(self):
        """Rerun selected comparison."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        history = self.settings.get_comparison_history()
        if current_row >= len(history):
            return

        item = history[current_row]
        paths = item.get("paths", [])
        is_directory = item.get("is_directory", False)

        self.compare_requested.emit(paths, is_directory)
        self.accept()

    def _clear_history(self):
        """Clear history."""
        self.settings.set_comparison_history([])
        self.table.setRowCount(0)
