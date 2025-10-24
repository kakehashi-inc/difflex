"""Home screen widget for starting new comparisons."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QGroupBox
)
from PySide6.QtCore import Signal, Qt


class PathInputWidget(QWidget):
    """Widget for inputting a file or directory path."""

    def __init__(self, label: str, is_file: bool = True, parent=None):
        """
        Initialize path input widget.

        Args:
            label: Label text
            is_file: True for file selection, False for directory
            parent: Parent widget
        """
        super().__init__(parent)
        self.is_file = is_file

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)
        layout.addWidget(label_widget)

        # Line edit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(
            "ファイルをドラッグ&ドロップ または ボタンで選択" if is_file
            else "ディレクトリをドラッグ&ドロップ または ボタンで選択"
        )
        self.line_edit.setAcceptDrops(True)
        self.line_edit.dragEnterEvent = self._drag_enter_event
        self.line_edit.dropEvent = self._drop_event
        layout.addWidget(self.line_edit, 1)

        # Browse button
        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self._browse)
        layout.addWidget(browse_btn)

        # Clear button
        clear_btn = QPushButton("✕")
        clear_btn.setMaximumWidth(30)
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(clear_btn)

    def _drag_enter_event(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop_event(self, event):
        """Handle drop event."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                self.line_edit.setText(path)
                event.acceptProposedAction()

    def _browse(self):
        """Open file/directory browser."""
        if self.is_file:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "ファイルを選択",
                "",
                "すべてのファイル (*.*)"
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self,
                "ディレクトリを選択"
            )

        if path:
            self.line_edit.setText(path)

    def get_path(self) -> str:
        """Get the current path."""
        return self.line_edit.text().strip()

    def set_path(self, path: str):
        """Set the path."""
        self.line_edit.setText(path)

    def clear(self):
        """Clear the path."""
        self.line_edit.clear()


class HomeWidget(QWidget):
    """Home screen widget."""

    compare_requested = Signal(list, bool)  # paths, is_directory
    history_requested = Signal()

    def __init__(self, parent=None):
        """Initialize home widget."""
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Difflex - ファイル/ディレクトリ比較")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # File comparison group
        file_group = QGroupBox("ファイル比較")
        file_layout = QVBoxLayout(file_group)

        self.file_inputs = []
        for i in range(3):
            input_widget = PathInputWidget(f"ファイル {i+1}:", is_file=True)
            input_widget.line_edit.textChanged.connect(self._update_buttons)
            self.file_inputs.append(input_widget)
            file_layout.addWidget(input_widget)

        self.file_compare_btn = QPushButton("ファイル比較を開始")
        self.file_compare_btn.setEnabled(False)
        self.file_compare_btn.clicked.connect(self._start_file_comparison)
        file_layout.addWidget(self.file_compare_btn)

        layout.addWidget(file_group)

        # Directory comparison group
        dir_group = QGroupBox("ディレクトリ比較")
        dir_layout = QVBoxLayout(dir_group)

        self.dir_inputs = []
        for i in range(3):
            input_widget = PathInputWidget(f"ディレクトリ {i+1}:", is_file=False)
            input_widget.line_edit.textChanged.connect(self._update_buttons)
            self.dir_inputs.append(input_widget)
            dir_layout.addWidget(input_widget)

        self.dir_compare_btn = QPushButton("ディレクトリ比較を開始")
        self.dir_compare_btn.setEnabled(False)
        self.dir_compare_btn.clicked.connect(self._start_dir_comparison)
        dir_layout.addWidget(self.dir_compare_btn)

        layout.addWidget(dir_group)

        # History button
        history_btn = QPushButton("比較履歴を表示")
        history_btn.clicked.connect(self.history_requested.emit)
        layout.addWidget(history_btn)

        layout.addStretch()

    def _update_buttons(self):
        """Update button states based on inputs."""
        # Check file inputs
        file_paths = [inp.get_path() for inp in self.file_inputs if inp.get_path()]
        self.file_compare_btn.setEnabled(len(file_paths) >= 2)

        # Check directory inputs
        dir_paths = [inp.get_path() for inp in self.dir_inputs if inp.get_path()]
        self.dir_compare_btn.setEnabled(len(dir_paths) >= 2)

    def _start_file_comparison(self):
        """Start file comparison."""
        paths = [inp.get_path() for inp in self.file_inputs if inp.get_path()]
        if len(paths) >= 2:
            self.compare_requested.emit(paths, False)
            # Clear inputs
            for inp in self.file_inputs:
                inp.clear()

    def _start_dir_comparison(self):
        """Start directory comparison."""
        paths = [inp.get_path() for inp in self.dir_inputs if inp.get_path()]
        if len(paths) >= 2:
            self.compare_requested.emit(paths, True)
            # Clear inputs
            for inp in self.dir_inputs:
                inp.clear()

    def load_from_history(self, paths: list[str], is_directory: bool):
        """
        Load paths from history.

        Args:
            paths: List of paths
            is_directory: True if directory comparison
        """
        inputs = self.dir_inputs if is_directory else self.file_inputs
        for i, path in enumerate(paths[:3]):
            if i < len(inputs):
                inputs[i].set_path(path)
