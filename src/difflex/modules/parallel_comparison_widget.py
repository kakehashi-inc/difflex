"""Parallel directory comparison widget with synchronized scrolling."""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QProgressBar, QHeaderView,
    QAbstractItemView, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from ..utils.file_types import FileTypeDetector, FileType
from ..utils.comparator import ComparisonResult
from ..utils.settings import Settings
from ..utils.i18n import tr


class SyncTreeWidget(QTreeWidget):
    """Tree widget with expansion signal."""

    itemExpanded = Signal(QTreeWidgetItem)
    itemCollapsed = Signal(QTreeWidgetItem)

    def __init__(self, parent=None):
        """Initialize sync tree widget."""
        super().__init__(parent)


class ParallelComparisonWidget(QWidget):
    """Widget for parallel directory comparison with synchronized views."""

    def __init__(
        self,
        paths: List[str],
        settings: Settings,
        parent=None
    ):
        """
        Initialize parallel comparison widget.

        Args:
            paths: List of directory paths (2 or 3)
            settings: Settings object
            parent: Parent widget
        """
        super().__init__(parent)
        self.paths = [Path(p) for p in paths]
        self.settings = settings
        self.worker = None
        self.items_map: Dict[str, Dict[str | int, QTreeWidgetItem]] = {}  # path -> {tree_idx or "result_N": item}
        self.pending_comparisons: Set[str] = set()  # Paths pending comparison

        # Setup file type detector
        text_exts = set(self.settings.get_text_extensions().split('\n'))
        text_exts = {ext.strip() for ext in text_exts if ext.strip()}
        image_exts = set(self.settings.get_image_extensions().split('\n'))
        image_exts = {ext.strip() for ext in image_exts if ext.strip()}
        self.detector = FileTypeDetector(text_exts, image_exts)

        self._setup_ui()
        self._scan_directories()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        layout.setSpacing(3)  # Reduce spacing between widgets

        # Compact header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        header = QLabel(tr("directory_comparison"))
        header.setStyleSheet("font-weight: bold; font-size: 11px;")
        header_layout.addWidget(header)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Create splitter for parallel trees
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.trees: List[SyncTreeWidget] = []
        self.result_trees: List[QTreeWidget] = []

        num_paths = len(self.paths)

        for i in range(num_paths):
            # Directory tree with multiple columns
            tree = SyncTreeWidget()
            tree.setColumnCount(3)  # Name, Size, Modified
            tree.setHeaderLabels([
                tr("name"),
                tr("file_size"),
                tr("modified_date")
            ])
            tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tree.setAlternatingRowColors(True)
            tree.itemDoubleClicked.connect(self._on_item_double_clicked)
            tree.itemExpanded.connect(lambda item, idx=i: self._on_item_expanded(item, idx))
            tree.itemCollapsed.connect(lambda item, idx=i: self._on_item_collapsed(item, idx))

            # Set column widths
            tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            tree.setColumnWidth(1, 100)  # Size column
            tree.setColumnWidth(2, 150)  # Modified column

            # Synchronize vertical scrolling
            tree.verticalScrollBar().valueChanged.connect(
                lambda value, idx=i: self._sync_scroll(value, idx)
            )

            self.trees.append(tree)
            splitter.addWidget(tree)

            # Comparison result tree (between trees)
            if i < num_paths - 1:
                result_tree = QTreeWidget()
                result_tree.setHeaderLabel(tr("comparison"))
                result_tree.setMaximumWidth(120)
                result_tree.setMinimumWidth(80)
                result_tree.setAlternatingRowColors(True)
                result_tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

                # Synchronize vertical scrolling
                result_tree.verticalScrollBar().valueChanged.connect(
                    lambda value, idx=i: self._sync_scroll(value, idx)
                )

                self.result_trees.append(result_tree)
                splitter.addWidget(result_tree)

        # Give splitter all remaining vertical space
        layout.addWidget(splitter, 1)

        # Compact button layout at bottom
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 3, 0, 0)

        self.compare_selected_btn = QPushButton(tr("compare_selected"))
        self.compare_selected_btn.setEnabled(False)
        self.compare_selected_btn.setMaximumHeight(28)
        self.compare_selected_btn.clicked.connect(self._compare_selected)
        button_layout.addWidget(self.compare_selected_btn)

        self.compare_all_btn = QPushButton(tr("compare_all"))
        self.compare_all_btn.setMaximumHeight(28)
        self.compare_all_btn.clicked.connect(self._compare_all)
        button_layout.addWidget(self.compare_all_btn)

        button_layout.addSpacing(10)

        self.expand_all_btn = QPushButton(tr("expand_all"))
        self.expand_all_btn.setMaximumHeight(28)
        self.expand_all_btn.clicked.connect(self._expand_all)
        button_layout.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton(tr("collapse_all"))
        self.collapse_all_btn.setMaximumHeight(28)
        self.collapse_all_btn.clicked.connect(self._collapse_all)
        button_layout.addWidget(self.collapse_all_btn)

        self.open_btn = QPushButton(tr("open_external"))
        self.open_btn.setEnabled(False)
        self.open_btn.setMaximumHeight(28)
        self.open_btn.clicked.connect(self._open_in_external_tool)
        button_layout.addWidget(self.open_btn)

        button_layout.addStretch()

        # Progress widgets (hidden initially)
        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("font-size: 10px;")
        self.progress_label.setVisible(False)
        button_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        button_layout.addSpacing(10)

        self.stop_btn = QPushButton(tr("stop"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMaximumHeight(28)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self._stop_comparison)
        button_layout.addWidget(self.stop_btn)

        layout.addLayout(button_layout)

    def _sync_scroll(self, value: int, _source_idx: int):
        """Synchronize scrolling across all trees."""
        # Block signals to prevent recursive updates
        for tree in self.trees:
            tree.verticalScrollBar().blockSignals(True)
        for result_tree in self.result_trees:
            result_tree.verticalScrollBar().blockSignals(True)

        # Set the scroll value directly
        for tree in self.trees:
            tree.verticalScrollBar().setValue(value)
        for result_tree in self.result_trees:
            result_tree.verticalScrollBar().setValue(value)

        # Unblock signals
        for tree in self.trees:
            tree.verticalScrollBar().blockSignals(False)
        for result_tree in self.result_trees:
            result_tree.verticalScrollBar().blockSignals(False)

    def _on_item_expanded(self, item: QTreeWidgetItem, tree_idx: int):
        """Handle item expansion - sync with other trees."""
        # Find corresponding items in other trees
        item_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_path:
            return

        for i, tree in enumerate(self.trees):
            if i != tree_idx:
                corresponding_item = self._find_item_by_path(tree, item_path)
                if corresponding_item:
                    corresponding_item.setExpanded(True)

    def _on_item_collapsed(self, item: QTreeWidgetItem, tree_idx: int):
        """Handle item collapse - sync with other trees."""
        # Find corresponding items in other trees
        item_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_path:
            return

        for i, tree in enumerate(self.trees):
            if i != tree_idx:
                corresponding_item = self._find_item_by_path(tree, item_path)
                if corresponding_item:
                    corresponding_item.setExpanded(False)

    def _find_item_by_path(self, tree: QTreeWidget, path: str) -> Optional[QTreeWidgetItem]:
        """Find item in tree by path."""
        # Recursive search
        def search_item(item: QTreeWidgetItem) -> Optional[QTreeWidgetItem]:
            if item.data(0, Qt.ItemDataRole.UserRole) == path:
                return item
            for i in range(item.childCount()):
                result = search_item(item.child(i))
                if result:
                    return result
            return None

        # Search in all top-level items
        for i in range(tree.topLevelItemCount()):
            top_item = tree.topLevelItem(i)
            if top_item is not None:
                result = search_item(top_item)
                if result:
                    return result

        return None

    def _expand_all(self):
        """Expand all items in all trees."""
        for tree in self.trees:
            tree.expandAll()
        for result_tree in self.result_trees:
            result_tree.expandAll()

    def _collapse_all(self):
        """Collapse all items in all trees."""
        for tree in self.trees:
            tree.collapseAll()
        for result_tree in self.result_trees:
            result_tree.collapseAll()

    def _scan_directories(self):
        """Scan directories and populate trees (without comparison)."""
        self.progress_label.setText(tr("preparing"))
        self.progress_bar.setMaximum(0)  # Indeterminate

        # Collect all files from all directories
        all_files = {}  # rel_path -> [Path | None, Path | None, ...]

        for dir_idx, directory in enumerate(self.paths):
            for root, _dirs, files in directory.walk():
                rel_root = root.relative_to(directory)

                # Add directories
                if str(rel_root) != ".":
                    if str(rel_root) not in all_files:
                        all_files[str(rel_root)] = [None] * len(self.paths)
                    all_files[str(rel_root)][dir_idx] = root

                # Add files
                for file in files:
                    file_path = root / file
                    rel_path = file_path.relative_to(directory)
                    rel_path_str = str(rel_path)

                    if rel_path_str not in all_files:
                        all_files[rel_path_str] = [None] * len(self.paths)

                    all_files[rel_path_str][dir_idx] = file_path

        # Populate trees
        for rel_path in sorted(all_files.keys()):
            paths = all_files[rel_path]
            self._add_item_to_trees(rel_path, paths)

        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.progress_label.setText(tr("complete"))

        # Expand first level
        for tree in self.trees:
            tree.expandToDepth(0)
        for result_tree in self.result_trees:
            result_tree.expandToDepth(0)

    def _add_item_to_trees(self, rel_path_str: str, paths: List[Optional[Path]]):
        """Add an item to all trees."""
        path_obj = Path(rel_path_str)
        parts = list(path_obj.parts)

        if not parts:
            return

        # Create or get parent items
        parent_items = [None] * len(self.trees)
        parent_result_items = [None] * len(self.result_trees)

        if len(parts) > 1:
            parent_path = str(Path(*parts[:-1]))
            if parent_path in self.items_map:
                parent_items = [self.items_map[parent_path].get(i) for i in range(len(self.trees))]
                parent_result_items = [self.items_map[parent_path].get(f"result_{i}") for i in range(len(self.result_trees))]

        # Determine if this is a directory
        is_dir = any(p and p.is_dir() for p in paths if p)

        # Create items in each tree
        tree_items: Dict[str | int, QTreeWidgetItem] = {}
        for i, tree in enumerate(self.trees):
            parent_item = parent_items[i]
            if parent_item is not None:
                item = QTreeWidgetItem(parent_item)
            else:
                item = QTreeWidgetItem(tree)

            # Set text and icon
            name = parts[-1]
            if is_dir:
                item.setText(0, f"📁 {name}")
                item.setText(1, "")  # No size for directories
                item.setText(2, "")  # No modified time for directories
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
                item.setForeground(0, QColor("#6495ED"))
            else:
                # Detect file type
                file_type = FileType.BINARY
                path_i = paths[i]
                if path_i is not None:
                    file_type = self.detector.detect(path_i)

                icon = "📄"
                if file_type == FileType.IMAGE:
                    icon = "🖼️"
                elif file_type == FileType.BINARY:
                    icon = "📦"

                item.setText(0, f"{icon} {name}")

                # Add file size and modified time
                if path_i is not None and path_i.exists():
                    try:
                        stat = path_i.stat()
                        # Format file size
                        size = stat.st_size
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        else:
                            size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"

                        item.setText(1, size_str)
                        item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                        # Format modified time
                        from datetime import datetime
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        item.setText(2, mtime.strftime("%Y/%m/%d %H:%M:%S"))
                    except Exception:
                        item.setText(1, "")
                        item.setText(2, "")
                else:
                    item.setText(1, "")
                    item.setText(2, "")

            # Mark if file exists in this location
            if paths[i]:
                item.setForeground(0, QColor("#FFFFFF") if self.settings.get_dark_mode() else QColor("#000000"))
            else:
                item.setForeground(0, QColor("#888888"))
                item.setFont(0, QFont("", -1, QFont.Weight.Light, True))  # Italic
                item.setText(0, f"× {name}")  # Show × for non-existent files

            # Store path data
            item.setData(0, Qt.ItemDataRole.UserRole, rel_path_str)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, paths[i])

            tree_items[i] = item

        # Create result items
        for i, result_tree in enumerate(self.result_trees):
            parent_result_item = parent_result_items[i]
            if parent_result_item is not None:
                result_item = QTreeWidgetItem(parent_result_item)
            else:
                result_item = QTreeWidgetItem(result_tree)

            # Show comparison status based on file existence
            left_path = paths[i]
            right_path = paths[i + 1] if i + 1 < len(paths) else None

            if left_path is None and right_path is None:
                # Both don't exist
                result_item.setText(0, "")
                result_item.setForeground(0, QColor("#888888"))
            elif left_path is None or right_path is None:
                # One side doesn't exist
                result_item.setText(0, "≠")
                result_item.setForeground(0, QColor("#F44336"))  # Red
                font = result_item.font(0)
                font.setBold(True)
                font.setPointSize(14)
                result_item.setFont(0, font)
            else:
                # Both exist - show as not compared yet
                result_item.setText(0, "")
                result_item.setForeground(0, QColor("#888888"))

            result_item.setTextAlignment(0, Qt.AlignmentFlag.AlignCenter)

            tree_items[f"result_{i}"] = result_item

        # Store items
        self.items_map[rel_path_str] = tree_items

    def _compare_selected(self):
        """Compare selected items."""
        # Get selected items from any tree
        paths_to_compare: Set[str] = set()

        for tree in self.trees:
            selected_items = tree.selectedItems()
            for item in selected_items:
                rel_path = item.data(0, Qt.ItemDataRole.UserRole)
                if rel_path:
                    # If it's a directory, add all files recursively
                    full_path = item.data(0, Qt.ItemDataRole.UserRole + 1)
                    if full_path and full_path.is_dir():
                        # Recursively add all files in directory
                        self._add_directory_files(item, paths_to_compare)
                    else:
                        paths_to_compare.add(rel_path)

        if paths_to_compare:
            self._start_comparison(list(paths_to_compare))

    def _add_directory_files(self, dir_item: QTreeWidgetItem, paths_set: Set[str]):
        """Recursively add all files in directory to paths set."""
        # Add current item if it's a file
        rel_path = dir_item.data(0, Qt.ItemDataRole.UserRole)
        full_path = dir_item.data(0, Qt.ItemDataRole.UserRole + 1)

        if rel_path and full_path and not full_path.is_dir():
            paths_set.add(rel_path)

        # Process children
        for i in range(dir_item.childCount()):
            child = dir_item.child(i)
            if child:
                self._add_directory_files(child, paths_set)

    def _compare_all(self):
        """Compare all items."""
        paths_to_compare = list(self.items_map.keys())
        self._start_comparison(paths_to_compare)

    def _start_comparison(self, paths_to_compare: List[str]):
        """Start comparison for specified paths."""
        if not paths_to_compare:
            return

        self.pending_comparisons = set(paths_to_compare)

        # Show progress widgets
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)
        self.stop_btn.setVisible(True)
        self.stop_btn.setEnabled(True)

        # Set progress
        self.progress_bar.setMaximum(len(paths_to_compare))
        self.progress_bar.setValue(0)
        self.progress_label.setText(tr("comparing", f"0/{len(paths_to_compare)}"))

        # Compare files
        from ..utils.comparator import TextComparator, ImageComparator, BinaryComparator

        text_threshold = self.settings.get_text_similarity_threshold()
        image_threshold = self.settings.get_image_similarity_threshold()
        binary_threshold = self.settings.get_binary_similarity_threshold()

        compared_count = 0
        for rel_path in paths_to_compare:
            if rel_path not in self.items_map:
                continue

            items = self.items_map[rel_path]

            # Get file paths from each tree
            file_paths = []
            for i in range(len(self.trees)):
                item = items.get(i)
                if item:
                    path = item.data(0, Qt.ItemDataRole.UserRole + 1)
                    file_paths.append(path)
                else:
                    file_paths.append(None)

            # Compare consecutive pairs
            for i in range(len(file_paths) - 1):
                path1 = file_paths[i]
                path2 = file_paths[i + 1]
                result_item = items.get(f"result_{i}")

                if not result_item:
                    continue

                # Skip if either path doesn't exist or is a directory
                if not path1 or not path2:
                    continue

                if not path1.exists() or not path2.exists():
                    continue

                if path1.is_dir() or path2.is_dir():
                    continue

                # Detect file type
                file_type = self.detector.detect(path1)

                # Compare files
                if file_type == FileType.TEXT:
                    result = TextComparator.compare(path1, path2, text_threshold)
                elif file_type == FileType.IMAGE:
                    result = ImageComparator.compare(path1, path2, image_threshold)
                else:
                    result = BinaryComparator.compare(path1, path2, binary_threshold)

                # Update result display with symbols and colors
                font = result_item.font(0)
                font.setBold(True)
                font.setPointSize(14)
                result_item.setFont(0, font)

                if result.status == ComparisonResult.IDENTICAL:
                    result_item.setText(0, "=")
                    result_item.setForeground(0, QColor("#4CAF50"))  # Green
                elif result.status == ComparisonResult.SIMILAR_EXIF:
                    result_item.setText(0, "≒")
                    result_item.setForeground(0, QColor("#2196F3"))  # Blue
                    result_item.setToolTip(0, "EXIF差異のみ")
                elif result.status == ComparisonResult.SIMILAR:
                    result_item.setText(0, "≒")
                    result_item.setForeground(0, QColor("#FFA500"))  # Orange
                    result_item.setToolTip(0, f"類似度: {result.similarity:.1f}%")
                else:
                    result_item.setText(0, "≠")
                    result_item.setForeground(0, QColor("#F44336"))  # Red
                    result_item.setToolTip(0, f"相違: {result.similarity:.1f}%")

            # Update progress
            compared_count += 1
            self.progress_bar.setValue(compared_count)
            self.progress_label.setText(tr("comparing", f"{compared_count}/{len(paths_to_compare)}"))

        # Hide progress widgets when complete
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)
        self.stop_btn.setVisible(False)
        self.stop_btn.setEnabled(False)

    def _stop_comparison(self):
        """Stop comparison."""
        if self.worker:
            self.worker.stop()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, _column: int):
        """Handle item double click."""
        # Check if it's a file (not directory)
        text = item.text(0)
        if text.startswith("📁"):
            # Toggle expansion
            item.setExpanded(not item.isExpanded())
        else:
            self._open_in_external_tool()

    def _open_in_external_tool(self):
        """Open selected files in external tool."""
        # Get file paths from all trees
        file_paths: List[Path] = []

        for tree in self.trees:
            selected_items = tree.selectedItems()
            if selected_items:
                item = selected_items[0]  # Use first selected item
                full_path = item.data(0, Qt.ItemDataRole.UserRole + 1)
                if full_path and full_path.exists() and not full_path.is_dir():
                    file_paths.append(full_path)
                    break  # Only get one path per tree

        if not file_paths:
            return

        # Get external tool settings
        text_tool = self.settings.get_external_text_tool()
        image_tool = self.settings.get_external_image_tool()
        binary_tool = self.settings.get_external_binary_tool()

        # Detect file type
        file_type = self.detector.detect(file_paths[0])

        # Select appropriate tool
        tool = ""
        if file_type == FileType.TEXT and text_tool:
            tool = text_tool
        elif file_type == FileType.IMAGE and image_tool:
            tool = image_tool
        elif binary_tool:
            tool = binary_tool

        if not tool:
            return

        # Build command and execute
        try:
            # Replace placeholders
            cmd = tool
            for i, path in enumerate(file_paths):
                cmd = cmd.replace(f"${i+1}", str(path))

            # Execute command
            subprocess.Popen(cmd, shell=True)
        except Exception as e:
            print(f"Failed to open external tool: {e}")

    def closeEvent(self, event):
        """Handle close event."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        event.accept()
