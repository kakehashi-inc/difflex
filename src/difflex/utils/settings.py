"""Settings management for difflex."""

import json
from pathlib import Path
from typing import Any
from PySide6.QtCore import QSettings


class Settings:
    """Application settings manager."""

    DEFAULT_TEXT_EXTENSIONS = """txt
py
java
c
cpp
h
hpp
cs
js
ts
html
css
xml
json
yaml
yml
md
rst
ini
cfg
conf
log
sh
bash
zsh
ps1
bat
cmd"""

    DEFAULT_IMAGE_EXTENSIONS = """jpg
jpeg
png
gif
bmp
tiff
tif
webp
ico
svg"""

    def __init__(self):
        """Initialize settings manager."""
        self._settings = QSettings("difflex", "difflex")

    def get_text_extensions(self) -> str:
        """Get text file extensions as newline-separated string."""
        return self._settings.value("text_extensions", self.DEFAULT_TEXT_EXTENSIONS)

    def set_text_extensions(self, extensions: str) -> None:
        """Set text file extensions."""
        self._settings.setValue("text_extensions", extensions)

    def get_image_extensions(self) -> str:
        """Get image file extensions as newline-separated string."""
        return self._settings.value("image_extensions", self.DEFAULT_IMAGE_EXTENSIONS)

    def set_image_extensions(self, extensions: str) -> None:
        """Set image file extensions."""
        self._settings.setValue("image_extensions", extensions)

    def get_dark_mode(self) -> bool:
        """Get dark mode setting."""
        return self._settings.value("dark_mode", True, type=bool)

    def set_dark_mode(self, enabled: bool) -> None:
        """Set dark mode."""
        self._settings.setValue("dark_mode", enabled)

    def get_text_similarity_threshold(self) -> float:
        """Get text similarity threshold (0-100)."""
        return self._settings.value("text_similarity_threshold", 95.0, type=float)

    def set_text_similarity_threshold(self, threshold: float) -> None:
        """Set text similarity threshold."""
        self._settings.setValue("text_similarity_threshold", threshold)

    def get_image_similarity_threshold(self) -> float:
        """Get image similarity threshold (0-100)."""
        return self._settings.value("image_similarity_threshold", 99.0, type=float)

    def set_image_similarity_threshold(self, threshold: float) -> None:
        """Set image similarity threshold."""
        self._settings.setValue("image_similarity_threshold", threshold)

    def get_binary_similarity_threshold(self) -> float:
        """Get binary similarity threshold (0-100)."""
        return self._settings.value("binary_similarity_threshold", 100.0, type=float)

    def set_binary_similarity_threshold(self, threshold: float) -> None:
        """Set binary similarity threshold."""
        self._settings.setValue("binary_similarity_threshold", threshold)

    def get_external_tool_config(self, file_type: str) -> dict[str, Any]:
        """
        Get external tool configuration for a file type.

        Args:
            file_type: 'text', 'image', or 'binary'

        Returns:
            Dictionary with 'executable', 'arg_before', 'arg1', 'arg2', 'arg3', 'arg_after', 'pack_args'
        """
        key = f"external_tool_{file_type}"
        default = {
            "executable": "",
            "arg_before": "",
            "arg1": "%s",
            "arg2": "%s",
            "arg3": "%s",
            "arg_after": "",
            "pack_args": False
        }
        value = self._settings.value(key, "")
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return default

    def set_external_tool_config(self, file_type: str, config: dict[str, Any]) -> None:
        """Set external tool configuration for a file type."""
        key = f"external_tool_{file_type}"
        self._settings.setValue(key, json.dumps(config))

    def get_comparison_history(self) -> list[dict[str, Any]]:
        """Get comparison history."""
        value = self._settings.value("comparison_history", "[]")
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []

    def set_comparison_history(self, history: list[dict[str, Any]]) -> None:
        """Set comparison history."""
        self._settings.setValue("comparison_history", json.dumps(history))

    def add_to_history(self, item: dict[str, Any]) -> None:
        """Add item to comparison history."""
        history = self.get_comparison_history()
        # Remove duplicates
        history = [h for h in history if h != item]
        # Add to beginning
        history.insert(0, item)
        # Keep only last 50 items
        history = history[:50]
        self.set_comparison_history(history)
