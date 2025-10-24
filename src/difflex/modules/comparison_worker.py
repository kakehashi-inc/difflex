"""Directory comparison worker thread."""

import os
from pathlib import Path
from typing import List, Tuple
from PySide6.QtCore import QThread, Signal

from ..utils.file_types import FileTypeDetector, FileType
from ..utils.comparator import TextComparator, ImageComparator, BinaryComparator, ComparisonResult


class FileComparisonItem:
    """Item representing a file comparison."""

    def __init__(self, name: str, paths: List[Path | None], file_type: FileType):
        """
        Initialize file comparison item.

        Args:
            name: Relative path/name of the file
            paths: List of file paths (None if file doesn't exist in that location)
            file_type: Type of the file
        """
        self.name = name
        self.paths = paths
        self.file_type = file_type
        self.results: List[ComparisonResult | None] = []

    def __repr__(self):
        """String representation."""
        return f"FileComparisonItem({self.name}, {len(self.paths)} paths)"


class DirectoryComparisonWorker(QThread):
    """Worker thread for directory comparison."""

    progress = Signal(int, int, str)  # current, total, message
    file_found = Signal(object)  # FileComparisonItem
    comparison_complete = Signal(object, list)  # FileComparisonItem, results
    finished = Signal()

    def __init__(
        self,
        directories: List[Path],
        file_type_detector: FileTypeDetector,
        text_threshold: float,
        image_threshold: float,
        binary_threshold: float
    ):
        """
        Initialize directory comparison worker.

        Args:
            directories: List of directory paths to compare
            file_type_detector: File type detector
            text_threshold: Text similarity threshold
            image_threshold: Image similarity threshold
            binary_threshold: Binary similarity threshold
        """
        super().__init__()
        self.directories = directories
        self.detector = file_type_detector
        self.text_threshold = text_threshold
        self.image_threshold = image_threshold
        self.binary_threshold = binary_threshold
        self._should_stop = False

    def stop(self):
        """Stop the worker."""
        self._should_stop = True

    def run(self):
        """Run the comparison."""
        try:
            # Collect all files
            all_files = self._collect_files()
            total = len(all_files)

            self.progress.emit(0, total, "ファイルを収集中...")

            # Process each file
            for idx, item in enumerate(all_files):
                if self._should_stop:
                    break

                self.progress.emit(idx, total, f"比較中: {item.name}")
                self.file_found.emit(item)

                # Compare files
                results = self._compare_item(item)
                item.results = results
                self.comparison_complete.emit(item, results)

            self.progress.emit(total, total, "完了")

        finally:
            self.finished.emit()

    def _collect_files(self) -> List[FileComparisonItem]:
        """Collect all files from directories."""
        # Map: relative_path -> list of absolute paths (or None)
        file_map = {}

        for dir_idx, directory in enumerate(self.directories):
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                rel_root = root_path.relative_to(directory)

                for file in files:
                    file_path = root_path / file
                    rel_path = rel_root / file
                    rel_path_str = str(rel_path)

                    if rel_path_str not in file_map:
                        file_map[rel_path_str] = [None] * len(self.directories)

                    file_map[rel_path_str][dir_idx] = file_path

        # Create comparison items
        items = []
        for rel_path, paths in sorted(file_map.items()):
            # Determine file type from first available file
            file_type = FileType.BINARY
            for path in paths:
                if path is not None:
                    file_type = self.detector.detect(path)
                    break

            items.append(FileComparisonItem(rel_path, paths, file_type))

        return items

    def _compare_item(self, item: FileComparisonItem) -> List[ComparisonResult | None]:
        """
        Compare files in the item.

        Returns:
            List of comparison results. For 2 files: [result], for 3 files: [result1_2, result2_3]
        """
        results = []

        # Compare consecutive pairs
        for i in range(len(item.paths) - 1):
            path1 = item.paths[i]
            path2 = item.paths[i + 1]

            if path1 is None or path2 is None:
                results.append(None)
                continue

            result = self._compare_files(path1, path2, item.file_type)
            results.append(result)

        return results

    def _compare_files(self, file1: Path, file2: Path, file_type: FileType) -> ComparisonResult:
        """Compare two files."""
        if file_type == FileType.TEXT:
            return TextComparator.compare(file1, file2, self.text_threshold)
        elif file_type == FileType.IMAGE:
            return ImageComparator.compare(file1, file2, self.image_threshold)
        else:
            return BinaryComparator.compare(file1, file2, self.binary_threshold)
