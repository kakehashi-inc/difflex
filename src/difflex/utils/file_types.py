"""File type detection utilities."""

from enum import Enum
from pathlib import Path


class FileType(Enum):
    """File type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    BINARY = "binary"


class FileTypeDetector:
    """Detects file types based on extensions."""

    def __init__(self, text_extensions: set[str] | None = None, image_extensions: set[str] | None = None):
        """
        Initialize file type detector.

        Args:
            text_extensions: Set of text file extensions (without dots)
            image_extensions: Set of image file extensions (without dots)
        """
        self.text_extensions = text_extensions or {
            'txt', 'py', 'java', 'c', 'cpp', 'h', 'hpp', 'cs', 'js', 'ts',
            'html', 'css', 'xml', 'json', 'yaml', 'yml', 'md', 'rst', 'ini',
            'cfg', 'conf', 'log', 'sh', 'bash', 'zsh', 'ps1', 'bat', 'cmd'
        }
        self.image_extensions = image_extensions or {
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'ico', 'svg'
        }

    def detect(self, file_path: Path | str) -> FileType:
        """
        Detect file type based on extension.

        Args:
            file_path: Path to the file

        Returns:
            FileType enum value
        """
        path = Path(file_path)
        ext = path.suffix.lower().lstrip('.')

        if ext in self.text_extensions:
            return FileType.TEXT
        elif ext in self.image_extensions:
            return FileType.IMAGE
        else:
            return FileType.BINARY

    def update_text_extensions(self, extensions: set[str]) -> None:
        """Update text file extensions."""
        self.text_extensions = extensions

    def update_image_extensions(self, extensions: set[str]) -> None:
        """Update image file extensions."""
        self.image_extensions = extensions
