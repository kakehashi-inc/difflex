"""File comparison utilities."""

import difflib
from pathlib import Path
from PIL import Image
import numpy as np


class ComparisonResult:
    """Result of a file comparison."""

    IDENTICAL = "="
    SIMILAR = "≒"
    SIMILAR_EXIF = "≒EX"
    DIFFERENT = "≠"

    def __init__(self, status: str, similarity: float = 100.0, details: str = ""):
        """
        Initialize comparison result.

        Args:
            status: One of IDENTICAL, SIMILAR, SIMILAR_EXIF, DIFFERENT
            similarity: Similarity percentage (0-100)
            details: Additional details about the comparison
        """
        self.status = status
        self.similarity = similarity
        self.details = details

    def __str__(self) -> str:
        """String representation."""
        if self.status == self.IDENTICAL:
            return self.IDENTICAL
        elif self.status == self.SIMILAR or self.status == self.SIMILAR_EXIF:
            return f"{self.status} ({self.similarity:.1f}%)"
        else:
            return self.DIFFERENT


class TextComparator:
    """Compare text files."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Normalize line endings
        lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        # Strip trailing whitespace from each line
        lines = [line.rstrip() for line in lines]
        return '\n'.join(lines)

    @staticmethod
    def compare(file1: Path, file2: Path, similarity_threshold: float = 95.0) -> ComparisonResult:
        """
        Compare two text files.

        Args:
            file1: First file path
            file2: Second file path
            similarity_threshold: Threshold for considering files similar (0-100)

        Returns:
            ComparisonResult object
        """
        try:
            # Read files with various encodings
            for encoding in ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932', 'latin-1']:
                try:
                    with open(file1, 'r', encoding=encoding) as f:
                        text1 = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, "Cannot decode file1")

            for encoding in ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932', 'latin-1']:
                try:
                    with open(file2, 'r', encoding=encoding) as f:
                        text2 = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, "Cannot decode file2")

            # Exact match
            if text1 == text2:
                return ComparisonResult(ComparisonResult.IDENTICAL, 100.0)

            # Normalize and compare
            norm1 = TextComparator.normalize_text(text1)
            norm2 = TextComparator.normalize_text(text2)

            if norm1 == norm2:
                return ComparisonResult(ComparisonResult.SIMILAR, 100.0, "Whitespace/newline differences only")

            # Calculate similarity
            similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio() * 100

            if similarity >= similarity_threshold:
                return ComparisonResult(ComparisonResult.SIMILAR, similarity, "Content mostly similar")
            else:
                return ComparisonResult(ComparisonResult.DIFFERENT, similarity, "Content differs significantly")

        except Exception as e:
            return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, f"Error: {str(e)}")


class ImageComparator:
    """Compare image files."""

    @staticmethod
    def compare(file1: Path, file2: Path, similarity_threshold: float = 99.0) -> ComparisonResult:
        """
        Compare two image files.

        Args:
            file1: First image path
            file2: Second image path
            similarity_threshold: Threshold for considering images similar (0-100)

        Returns:
            ComparisonResult object
        """
        try:
            # Binary comparison first
            with open(file1, 'rb') as f:
                data1 = f.read()
            with open(file2, 'rb') as f:
                data2 = f.read()

            if data1 == data2:
                return ComparisonResult(ComparisonResult.IDENTICAL, 100.0)

            # Open images
            img1 = Image.open(file1)
            img2 = Image.open(file2)

            # Check dimensions
            if img1.size != img2.size:
                return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, "Different dimensions")

            # Convert to same mode
            if img1.mode != img2.mode:
                img2 = img2.convert(img1.mode)

            # Compare pixels
            arr1 = np.array(img1)
            arr2 = np.array(img2)

            if np.array_equal(arr1, arr2):
                # Pixels identical but file different (EXIF, metadata, etc.)
                return ComparisonResult(ComparisonResult.SIMILAR_EXIF, 100.0, "Pixel data identical, metadata differs")

            # Calculate pixel difference
            diff = np.abs(arr1.astype(float) - arr2.astype(float))
            max_diff = 255.0 if arr1.dtype == np.uint8 else float(np.iinfo(arr1.dtype).max)
            similarity = 100.0 - (np.mean(diff) / max_diff * 100.0)

            if similarity >= similarity_threshold:
                return ComparisonResult(ComparisonResult.SIMILAR, similarity, "Pixels mostly similar")
            else:
                return ComparisonResult(ComparisonResult.DIFFERENT, similarity, "Pixels differ significantly")

        except Exception as e:
            return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, f"Error: {str(e)}")


class BinaryComparator:
    """Compare binary files."""

    @staticmethod
    def compare(file1: Path, file2: Path, similarity_threshold: float = 100.0) -> ComparisonResult:
        """
        Compare two binary files.

        Args:
            file1: First file path
            file2: Second file path
            similarity_threshold: Threshold for considering files similar (0-100)

        Returns:
            ComparisonResult object
        """
        try:
            with open(file1, 'rb') as f:
                data1 = f.read()
            with open(file2, 'rb') as f:
                data2 = f.read()

            if data1 == data2:
                return ComparisonResult(ComparisonResult.IDENTICAL, 100.0)

            # Calculate byte-level similarity
            len1 = len(data1)
            len2 = len(data2)

            if len1 == 0 and len2 == 0:
                return ComparisonResult(ComparisonResult.IDENTICAL, 100.0)

            if len1 == 0 or len2 == 0:
                return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, "One file is empty")

            # Compare byte by byte
            min_len = min(len1, len2)
            matching_bytes = sum(1 for i in range(min_len) if data1[i] == data2[i])

            # Account for length difference
            max_len = max(len1, len2)
            similarity = (matching_bytes / max_len) * 100.0

            if similarity >= similarity_threshold:
                return ComparisonResult(ComparisonResult.SIMILAR, similarity, "Binary data mostly similar")
            else:
                return ComparisonResult(ComparisonResult.DIFFERENT, similarity, "Binary data differs")

        except Exception as e:
            return ComparisonResult(ComparisonResult.DIFFERENT, 0.0, f"Error: {str(e)}")
