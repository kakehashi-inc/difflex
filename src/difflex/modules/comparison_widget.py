"""Comparison tab widget."""

import subprocess
from pathlib import Path
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QProgressBar, QHeaderView,
    QAbstractItemView, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ..utils.file_types import FileTypeDetector, FileType
from ..utils.comparator import ComparisonResult
from ..utils.settings import Settings
from ..utils.i18n import tr
from .comparison_worker import DirectoryComparisonWorker, FileComparisonItem


class ComparisonWidget(QWidget):
    """Widget for displaying file/directory comparison."""

    def __init__(
        self,
        paths: List[str],
        is_directory: bool,
        settings: Settings,
        parent=None
    ):
        """
        Initialize comparison widget.

        Args:
            paths: List of file or directory paths
            is_directory: True if comparing directories
            settings: Settings object
            parent: Parent widget
        """
        super().__init__(parent)
        self.paths = [Path(p) for p in paths]
        self.is_directory = is_directory
        self.settings = settings
        self.worker = None

        # Setup file type detector
        text_exts = set(self.settings.get_text_extensions().split('\n'))
        text_exts = {ext.strip() for ext in text_exts if ext.strip()}
        image_exts = set(self.settings.get_image_extensions().split('\n'))
        image_exts = {ext.strip() for ext in image_exts if ext.strip()}
        self.detector = FileTypeDetector(text_exts, image_exts)

        self._setup_ui()

        # Start comparison
        if is_directory:
            self._start_directory_comparison()
        else:
            self._start_file_comparison()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Header
        comp_type = tr("directory_comparison") if self.is_directory else tr("file_comparison")
        header = QLabel(
            comp_type + ": " +
            " vs ".join([p.name for p in self.paths])
        )
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel(tr("preparing"))
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        # Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        # Setup columns
        num_paths = len(self.paths)
        num_result_cols = num_paths - 1
        total_cols = 1 + num_paths + num_result_cols  # name + paths + results

        self.table.setColumnCount(total_cols)
        headers = [tr("file_name")]

        for i, path in enumerate(self.paths):
            headers.append(tr("comparison_location", i+1))
            if i < num_paths - 1:
                headers.append(tr("comparison_result"))

        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.open_btn = QPushButton(tr("open_external_tool"))
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_in_external_tool)
        button_layout.addWidget(self.open_btn)

        button_layout.addStretch()

        self.stop_btn = QPushButton(tr("stop"))
        self.stop_btn.clicked.connect(self._stop_comparison)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

    def _start_file_comparison(self):
        """Start file comparison."""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.progress_label.setText(tr("file_comparison_complete"))
        self.stop_btn.setEnabled(False)

        # Add single row
        self.table.setRowCount(1)

        # File name
        self.table.setItem(0, 0, QTableWidgetItem(tr("file_comparison")))

        # Paths
        for i, path in enumerate(self.paths):
            self.table.setItem(0, 1 + i * 2, QTableWidgetItem(str(path)))

        # Compare files
        file_type = self.detector.detect(self.paths[0])

        from ..utils.comparator import TextComparator, ImageComparator, BinaryComparator

        text_threshold = self.settings.get_text_similarity_threshold()
        image_threshold = self.settings.get_image_similarity_threshold()
        binary_threshold = self.settings.get_binary_similarity_threshold()

        for i in range(len(self.paths) - 1):
            path1 = self.paths[i]
            path2 = self.paths[i + 1]

            if file_type == FileType.TEXT:
                result = TextComparator.compare(path1, path2, text_threshold)
            elif file_type == FileType.IMAGE:
                result = ImageComparator.compare(path1, path2, image_threshold)
            else:
                result = BinaryComparator.compare(path1, path2, binary_threshold)

            item = QTableWidgetItem(str(result))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Color code
            if result.status == ComparisonResult.IDENTICAL:
                item.setBackground(QColor(200, 255, 200))
            elif result.status in (ComparisonResult.SIMILAR, ComparisonResult.SIMILAR_EXIF):
                item.setBackground(QColor(255, 255, 200))
            else:
                item.setBackground(QColor(255, 200, 200))

            self.table.setItem(0, 2 + i * 2, item)

        self.open_btn.setEnabled(True)

    def _start_directory_comparison(self):
        """Start directory comparison."""
        text_threshold = self.settings.get_text_similarity_threshold()
        image_threshold = self.settings.get_image_similarity_threshold()
        binary_threshold = self.settings.get_binary_similarity_threshold()

        self.worker = DirectoryComparisonWorker(
            self.paths,
            self.detector,
            text_threshold,
            image_threshold,
            binary_threshold
        )

        self.worker.progress.connect(self._on_progress)
        self.worker.file_found.connect(self._on_file_found)
        self.worker.comparison_complete.connect(self._on_comparison_complete)
        self.worker.finished.connect(self._on_finished)

        self.worker.start()

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(message)

    def _on_file_found(self, item: FileComparisonItem):
        """Handle file found."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # File name
        self.table.setItem(row, 0, QTableWidgetItem(item.name))

        # Paths
        num_paths = len(item.paths)
        for i, path in enumerate(item.paths):
            path_str = str(path) if path else ""
            path_item = QTableWidgetItem(path_str)
            if not path:
                path_item.setBackground(QColor(220, 220, 220))
            self.table.setItem(row, 1 + i * 2, path_item)

    def _on_comparison_complete(self, item: FileComparisonItem, results: List):
        """Handle comparison complete."""
        # Find the row for this item
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == item.name:
                # Add results
                for i, result in enumerate(results):
                    if result is None:
                        result_item = QTableWidgetItem("-")
                        result_item.setBackground(QColor(220, 220, 220))
                    else:
                        result_item = QTableWidgetItem(str(result))

                        # Color code
                        if result.status == ComparisonResult.IDENTICAL:
                            result_item.setBackground(QColor(200, 255, 200))
                        elif result.status in (ComparisonResult.SIMILAR, ComparisonResult.SIMILAR_EXIF):
                            result_item.setBackground(QColor(255, 255, 200))
                        else:
                            result_item.setBackground(QColor(255, 200, 200))

                    result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, 2 + i * 2, result_item)
                break

    def _on_finished(self):
        """Handle worker finished."""
        self.stop_btn.setEnabled(False)
        self.open_btn.setEnabled(True)

    def _stop_comparison(self):
        """Stop comparison."""
        if self.worker:
            self.worker.stop()

    def _on_row_double_clicked(self, index):
        """Handle row double click."""
        self._open_in_external_tool()

    def _open_in_external_tool(self):
        """Open selected files in external tool."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        # Get file paths from the row
        file_paths = []
        num_paths = len(self.paths)

        if self.is_directory:
            # Get paths from table cells
            for i in range(num_paths):
                path_text = self.table.item(current_row, 1 + i * 2).text()
                if path_text:
                    file_paths.append(path_text)
                else:
                    file_paths.append(None)
        else:
            # Use original paths
            file_paths = [str(p) for p in self.paths]

        # Determine file type
        file_type = None
        for path in file_paths:
            if path:
                detected = self.detector.detect(Path(path))
                if detected == FileType.TEXT:
                    file_type = "text"
                elif detected == FileType.IMAGE:
                    file_type = "image"
                else:
                    file_type = "binary"
                break

        if not file_type:
            return

        # Get external tool config
        config = self.settings.get_external_tool_config(file_type)
        executable = config.get("executable", "").strip()

        if not executable:
            return

        # Build command
        args = []

        arg_before = config.get("arg_before", "").strip()
        if arg_before:
            args.append(arg_before)

        arg_templates = [
            config.get("arg1", "%s"),
            config.get("arg2", "%s"),
            config.get("arg3", "%s")
        ]

        pack_args = config.get("pack_args", False)

        if pack_args:
            # Pack arguments (remove gaps)
            for path in file_paths:
                if path and arg_templates:
                    template = arg_templates.pop(0)
                    args.append(template.replace("%s", path))
        else:
            # Use arguments as-is
            for i, (path, template) in enumerate(zip(file_paths, arg_templates)):
                if i < len(file_paths) and file_paths[i]:
                    args.append(template.replace("%s", file_paths[i]))

        arg_after = config.get("arg_after", "").strip()
        if arg_after:
            args.append(arg_after)

        # Execute
        try:
            subprocess.Popen([executable] + args)
        except Exception as e:
            print(f"Failed to open external tool: {e}")

    def closeEvent(self, event):
        """Handle close event."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        event.accept()
