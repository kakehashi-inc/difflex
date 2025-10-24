"""Simple file comparison widget."""

import subprocess
from pathlib import Path
from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ..utils.file_types import FileTypeDetector, FileType
from ..utils.comparator import ComparisonResult, TextComparator, ImageComparator, BinaryComparator
from ..utils.settings import Settings
from ..utils.i18n import tr


class FileComparisonWidget(QWidget):
    """Widget for displaying file comparison."""

    def __init__(
        self,
        paths: List[str],
        settings: Settings,
        parent=None
    ):
        """
        Initialize file comparison widget.

        Args:
            paths: List of file paths
            settings: Settings object
            parent: Parent widget
        """
        super().__init__(parent)
        self.paths = [Path(p) for p in paths]
        self.settings = settings

        # Setup file type detector
        text_exts = set(self.settings.get_text_extensions().split('\n'))
        text_exts = {ext.strip() for ext in text_exts if ext.strip()}
        image_exts = set(self.settings.get_image_extensions().split('\n'))
        image_exts = {ext.strip() for ext in image_exts if ext.strip()}
        self.detector = FileTypeDetector(text_exts, image_exts)

        self._setup_ui()
        self._compare_files()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            tr("file_comparison_title", " vs ".join([p.name for p in self.paths]))
        )
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        # Setup columns
        num_paths = len(self.paths)
        num_result_cols = num_paths - 1
        total_cols = 1 + num_paths + num_result_cols  # name + paths + results

        self.table.setColumnCount(total_cols)
        headers = [tr("item")]

        for i in range(num_paths):
            headers.append(tr("file_label", str(i+1)))
            if i < num_paths - 1:
                headers.append(tr("comparison_result"))

        self.table.setHorizontalHeaderLabels(headers)

        # Set column widths
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 100)

        for i in range(1, total_cols):
            if (i - 1) % 2 == 1:  # Result columns
                self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.table.setColumnWidth(i, 120)
            else:  # Path columns
                self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        self.open_btn = QPushButton(tr("open_external"))
        self.open_btn.clicked.connect(self._open_in_external_tool)
        button_layout.addWidget(self.open_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _compare_files(self):
        """Compare files and display results."""
        # Add rows for different aspects
        aspects = [
            (tr("file_name"), [p.name for p in self.paths]),
            (tr("file_path"), [str(p) for p in self.paths]),
            (tr("file_size"), [f"{p.stat().st_size:,} {tr('bytes')}" if p.exists() else "N/A" for p in self.paths]),
        ]

        self.table.setRowCount(len(aspects) + 1)  # +1 for comparison result

        for row, (aspect_name, values) in enumerate(aspects):
            # Aspect name
            item = QTableWidgetItem(aspect_name)
            item.setFont(item.font())
            self.table.setItem(row, 0, item)

            # Values
            for i, value in enumerate(values):
                col_idx = 1 + i * 2
                self.table.setItem(row, col_idx, QTableWidgetItem(value))

        # Compare files
        file_type = self.detector.detect(self.paths[0])

        text_threshold = self.settings.get_text_similarity_threshold()
        image_threshold = self.settings.get_image_similarity_threshold()
        binary_threshold = self.settings.get_binary_similarity_threshold()

        # Comparison result row
        result_row = len(aspects)
        item = QTableWidgetItem(tr("comparison_result"))
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.table.setItem(result_row, 0, item)

        for i in range(len(self.paths) - 1):
            path1 = self.paths[i]
            path2 = self.paths[i + 1]

            if file_type == FileType.TEXT:
                result = TextComparator.compare(path1, path2, text_threshold)
            elif file_type == FileType.IMAGE:
                result = ImageComparator.compare(path1, path2, image_threshold)
            else:
                result = BinaryComparator.compare(path1, path2, binary_threshold)

            col_idx = 2 + i * 2

            # Use symbols and colors for better visibility
            result_item = QTableWidgetItem()

            if result.status == ComparisonResult.IDENTICAL:
                result_item.setText(tr("identical"))
                result_item.setForeground(QColor("#4CAF50"))
            elif result.status == ComparisonResult.SIMILAR_EXIF:
                result_item.setText(tr("similar_exif"))
                result_item.setForeground(QColor("#2196F3"))
            elif result.status == ComparisonResult.SIMILAR:
                result_item.setText(tr("similar_with_percent", f"≒ {tr('similar')} ({result.similarity:.1f}%)"))
                result_item.setForeground(QColor("#FFA500"))
            else:
                result_item.setText(tr("different_with_percent", f"✗ {tr('different')} ({result.similarity:.1f}%)"))
                result_item.setForeground(QColor("#F44336"))

            result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = result_item.font()
            font.setBold(True)
            result_item.setFont(font)

            self.table.setItem(result_row, col_idx, result_item)

            # Add details if available
            if result.details:
                result_item.setToolTip(result.details)

    def _on_row_double_clicked(self, index):
        """Handle row double click."""
        self._open_in_external_tool()

    def _open_in_external_tool(self):
        """Open files in external tool."""
        # Determine file type
        file_type = self.detector.detect(self.paths[0])

        if file_type == FileType.TEXT:
            file_type_str = "text"
        elif file_type == FileType.IMAGE:
            file_type_str = "image"
        else:
            file_type_str = "binary"

        # Get external tool config
        config = self.settings.get_external_tool_config(file_type_str)
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
        file_paths = [str(p) for p in self.paths]

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
