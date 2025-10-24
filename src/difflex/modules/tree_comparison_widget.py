"""Tree-based comparison widget for directory comparison."""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from ..utils.file_types import FileTypeDetector, FileType
from ..utils.comparator import ComparisonResult
from ..utils.settings import Settings
from ..utils.i18n import tr
from .comparison_worker import DirectoryComparisonWorker, FileComparisonItem


class ComparisonTreeWidget(QWidget):
    """Widget for displaying directory comparison in tree view."""

    def __init__(
        self,
        paths: List[str],
        settings: Settings,
        parent=None
    ):
        """
        Initialize comparison tree widget.

        Args:
            paths: List of directory paths
            settings: Settings object
            parent: Parent widget
        """
        super().__init__(parent)
        self.paths = [Path(p) for p in paths]
        self.settings = settings
        self.worker = None
        self.items_map: Dict[str, QTreeWidgetItem] = {}

        # Setup file type detector
        text_exts = set(self.settings.get_text_extensions().split('\n'))
        text_exts = {ext.strip() for ext in text_exts if ext.strip()}
        image_exts = set(self.settings.get_image_extensions().split('\n'))
        image_exts = {ext.strip() for ext in image_exts if ext.strip()}
        self.detector = FileTypeDetector(text_exts, image_exts)

        self._setup_ui()
        self._start_directory_comparison()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            tr("directory_comparison") + ": " +
            " vs ".join([p.name for p in self.paths])
        )
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel(tr("preparing"))
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Setup columns
        num_paths = len(self.paths)
        num_result_cols = num_paths - 1
        total_cols = 1 + num_paths + num_result_cols  # name + paths + results

        self.tree.setColumnCount(total_cols)
        headers = [tr("file_directory")]

        for i, path in enumerate(self.paths):
            headers.append(tr("comparison_location", i+1))
            if i < num_paths - 1:
                headers.append(tr("comparison_result"))

        self.tree.setHeaderLabels(headers)

        # Set column widths
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, total_cols):
            if (i - 1) % 2 == 1:  # Result columns
                self.tree.header().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.tree.setColumnWidth(i, 80)
            else:  # Path columns
                self.tree.header().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.tree.setColumnWidth(i, 150)

        layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()

        self.expand_all_btn = QPushButton(tr("expand_all"))
        self.expand_all_btn.clicked.connect(self.tree.expandAll)
        button_layout.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton(tr("collapse_all"))
        self.collapse_all_btn.clicked.connect(self.tree.collapseAll)
        button_layout.addWidget(self.collapse_all_btn)

        self.open_btn = QPushButton(tr("open_external_tool"))
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self._open_in_external_tool)
        button_layout.addWidget(self.open_btn)

        button_layout.addStretch()

        self.stop_btn = QPushButton(tr("stop"))
        self.stop_btn.clicked.connect(self._stop_comparison)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

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

    def _get_or_create_parent_item(self, path_parts: List[str]) -> Optional[QTreeWidgetItem]:
        """
        Get or create parent tree item for the given path.

        Args:
            path_parts: List of path components

        Returns:
            Parent tree item or None for root
        """
        if not path_parts:
            return None

        parent = None
        current_path = ""

        for part in path_parts:
            current_path = f"{current_path}/{part}" if current_path else part

            if current_path not in self.items_map:
                # Create directory item
                if parent is None:
                    item = QTreeWidgetItem(self.tree)
                else:
                    item = QTreeWidgetItem(parent)

                item.setText(0, f"📁 {part}")

                # Make directory items bold
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)

                # Set icon color for directory
                item.setForeground(0, QColor("#6495ED"))

                self.items_map[current_path] = item
                parent = item
            else:
                parent = self.items_map[current_path]

        return parent

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(message)

    def _on_file_found(self, item: FileComparisonItem):
        """Handle file found."""
        # Parse path to get directory structure
        path_obj = Path(item.name)
        path_parts = list(path_obj.parts[:-1])  # All except filename
        filename = path_obj.name

        # Get or create parent
        parent = self._get_or_create_parent_item(path_parts)

        # Create file item
        if parent is None:
            tree_item = QTreeWidgetItem(self.tree)
        else:
            tree_item = QTreeWidgetItem(parent)

        # Set filename with icon
        file_icon = "📄"
        if item.file_type == FileType.IMAGE:
            file_icon = "🖼️"
        elif item.file_type == FileType.BINARY:
            file_icon = "📦"

        tree_item.setText(0, f"{file_icon} {filename}")

        # Store the item for later updates
        self.items_map[item.name] = tree_item

        # Add path information
        num_paths = len(item.paths)
        for i, path in enumerate(item.paths):
            col_idx = 1 + i * 2
            if path:
                tree_item.setText(col_idx, "○")
                tree_item.setForeground(col_idx, QColor("#4CAF50"))
            else:
                tree_item.setText(col_idx, "×")
                tree_item.setForeground(col_idx, QColor("#888888"))
            tree_item.setTextAlignment(col_idx, Qt.AlignmentFlag.AlignCenter)

        # Store file paths in item data
        tree_item.setData(0, Qt.ItemDataRole.UserRole, item.paths)

    def _on_comparison_complete(self, item: FileComparisonItem, results: List):
        """Handle comparison complete."""
        tree_item = self.items_map.get(item.name)
        if not tree_item:
            return

        # Add results with color-coded text
        for i, result in enumerate(results):
            col_idx = 2 + i * 2

            if result is None:
                tree_item.setText(col_idx, "-")
                tree_item.setForeground(col_idx, QColor("#888888"))
            else:
                # Use symbols and colors for better visibility
                if result.status == ComparisonResult.IDENTICAL:
                    tree_item.setText(col_idx, tr("identical"))
                    tree_item.setForeground(col_idx, QColor("#4CAF50"))
                elif result.status == ComparisonResult.SIMILAR_EXIF:
                    tree_item.setText(col_idx, tr("similar_exif"))
                    tree_item.setForeground(col_idx, QColor("#2196F3"))
                elif result.status == ComparisonResult.SIMILAR:
                    tree_item.setText(col_idx, tr("similar_with_percent", result.similarity))
                    tree_item.setForeground(col_idx, QColor("#FFA500"))
                else:
                    tree_item.setText(col_idx, tr("different"))
                    tree_item.setForeground(col_idx, QColor("#F44336"))

            tree_item.setTextAlignment(col_idx, Qt.AlignmentFlag.AlignCenter)

    def _on_finished(self):
        """Handle worker finished."""
        self.stop_btn.setEnabled(False)
        self.open_btn.setEnabled(True)
        self.tree.expandToDepth(0)  # Expand first level by default

    def _stop_comparison(self):
        """Stop comparison."""
        if self.worker:
            self.worker.stop()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item double click."""
        # Only open files, not directories
        text = item.text(0)
        if text.startswith("📁"):
            return

        self._open_in_external_tool()

    def _open_in_external_tool(self):
        """Open selected files in external tool."""
        current_item = self.tree.currentItem()
        if not current_item:
            return

        # Check if it's a file (not directory)
        if current_item.text(0).startswith("📁"):
            return

        # Get file paths from item data
        file_paths = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not file_paths:
            return

        # Filter out None values but keep track of positions
        valid_paths = [str(p) if p else None for p in file_paths]

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
            for path in valid_paths:
                if path and arg_templates:
                    template = arg_templates.pop(0)
                    args.append(template.replace("%s", path))
        else:
            # Use arguments as-is
            for i, (path, template) in enumerate(zip(valid_paths, arg_templates)):
                if i < len(valid_paths) and valid_paths[i]:
                    args.append(template.replace("%s", valid_paths[i]))

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
