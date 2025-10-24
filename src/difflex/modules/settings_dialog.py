"""Settings dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QCheckBox, QSpinBox, QGroupBox, QLineEdit,
    QFileDialog, QTabWidget, QWidget, QFormLayout, QComboBox
)
from PySide6.QtCore import Signal

from ..utils.settings import Settings
from ..utils.i18n import tr


class ExternalToolWidget(QWidget):
    """Widget for configuring external tool."""

    def __init__(self, file_type: str, parent=None):
        """
        Initialize external tool widget.

        Args:
            file_type: 'text', 'image', or 'binary'
            parent: Parent widget
        """
        super().__init__(parent)
        self.file_type = file_type
        self._setup_ui()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QFormLayout(self)

        # Executable
        exec_layout = QHBoxLayout()
        self.executable_edit = QLineEdit()
        exec_layout.addWidget(self.executable_edit, 1)
        browse_btn = QPushButton(tr("browse"))
        browse_btn.clicked.connect(self._browse_executable)
        exec_layout.addWidget(browse_btn)
        layout.addRow(tr("executable"), exec_layout)

        # Arguments
        self.arg_before_edit = QLineEdit()
        self.arg_before_edit.setPlaceholderText(tr("arg_before_example"))
        layout.addRow(tr("arg_before"), self.arg_before_edit)

        self.arg1_edit = QLineEdit()
        self.arg1_edit.setPlaceholderText("%s")
        layout.addRow(tr("arg_file1"), self.arg1_edit)

        self.arg2_edit = QLineEdit()
        self.arg2_edit.setPlaceholderText("%s")
        layout.addRow(tr("arg_file2"), self.arg2_edit)

        self.arg3_edit = QLineEdit()
        self.arg3_edit.setPlaceholderText("%s")
        layout.addRow(tr("arg_file3"), self.arg3_edit)

        self.arg_after_edit = QLineEdit()
        self.arg_after_edit.setPlaceholderText(tr("arg_after_example"))
        layout.addRow(tr("arg_after"), self.arg_after_edit)

        # Pack args option
        self.pack_args_check = QCheckBox(tr("pack_args"))
        self.pack_args_check.setToolTip(tr("pack_args_tooltip"))
        layout.addRow("", self.pack_args_check)

    def _browse_executable(self):
        """Browse for executable."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("select_executable"),
            "",
            tr("executable_files")
        )
        if path:
            self.executable_edit.setText(path)

    def load_config(self, config: dict):
        """Load configuration."""
        self.executable_edit.setText(config.get("executable", ""))
        self.arg_before_edit.setText(config.get("arg_before", ""))
        self.arg1_edit.setText(config.get("arg1", "%s"))
        self.arg2_edit.setText(config.get("arg2", "%s"))
        self.arg3_edit.setText(config.get("arg3", "%s"))
        self.arg_after_edit.setText(config.get("arg_after", ""))
        self.pack_args_check.setChecked(config.get("pack_args", False))

    def get_config(self) -> dict:
        """Get configuration."""
        return {
            "executable": self.executable_edit.text().strip(),
            "arg_before": self.arg_before_edit.text().strip(),
            "arg1": self.arg1_edit.text().strip() or "%s",
            "arg2": self.arg2_edit.text().strip() or "%s",
            "arg3": self.arg3_edit.text().strip() or "%s",
            "arg_after": self.arg_after_edit.text().strip(),
            "pack_args": self.pack_args_check.isChecked()
        }


class SettingsDialog(QDialog):
    """Settings dialog."""

    language_changed = Signal()  # Signal emitted when language changes

    def __init__(self, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumSize(600, 500)
        self.settings = Settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup user interface."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # Language selection
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel(tr("language_label")))
        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("language_ja"), "ja-JP")
        self.language_combo.addItem(tr("language_en"), "en-US")
        self.language_combo.addItem(tr("language_auto"), "")
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        general_layout.addLayout(lang_layout)

        # Dark mode
        self.dark_mode_check = QCheckBox(tr("dark_mode"))
        general_layout.addWidget(self.dark_mode_check)

        # Text extensions
        ext_group = QGroupBox(tr("text_extensions"))
        ext_layout = QVBoxLayout(ext_group)
        ext_layout.addWidget(QLabel(tr("extension_help")))
        self.text_ext_edit = QTextEdit()
        self.text_ext_edit.setMaximumHeight(100)
        ext_layout.addWidget(self.text_ext_edit)
        general_layout.addWidget(ext_group)

        # Image extensions
        img_group = QGroupBox(tr("image_extensions"))
        img_layout = QVBoxLayout(img_group)
        img_layout.addWidget(QLabel(tr("extension_help")))
        self.image_ext_edit = QTextEdit()
        self.image_ext_edit.setMaximumHeight(100)
        img_layout.addWidget(self.image_ext_edit)
        general_layout.addWidget(img_group)

        general_layout.addStretch()
        tabs.addTab(general_tab, tr("general"))

        # Similarity tab
        similarity_tab = QWidget()
        similarity_layout = QFormLayout(similarity_tab)

        self.text_threshold_spin = QSpinBox()
        self.text_threshold_spin.setRange(0, 100)
        self.text_threshold_spin.setSuffix("%")
        similarity_layout.addRow(tr("text_threshold"), self.text_threshold_spin)

        self.image_threshold_spin = QSpinBox()
        self.image_threshold_spin.setRange(0, 100)
        self.image_threshold_spin.setSuffix("%")
        similarity_layout.addRow(tr("image_threshold"), self.image_threshold_spin)

        self.binary_threshold_spin = QSpinBox()
        self.binary_threshold_spin.setRange(0, 100)
        self.binary_threshold_spin.setSuffix("%")
        similarity_layout.addRow(tr("binary_threshold"), self.binary_threshold_spin)

        tabs.addTab(similarity_tab, tr("similarity"))

        # External tools tab
        tools_tab = QWidget()
        tools_layout = QVBoxLayout(tools_tab)

        tool_tabs = QTabWidget()

        self.text_tool_widget = ExternalToolWidget("text")
        tool_tabs.addTab(self.text_tool_widget, tr("tool_text"))

        self.image_tool_widget = ExternalToolWidget("image")
        tool_tabs.addTab(self.image_tool_widget, tr("tool_image"))

        self.binary_tool_widget = ExternalToolWidget("binary")
        tool_tabs.addTab(self.binary_tool_widget, tr("tool_other"))

        tools_layout.addWidget(tool_tabs)
        tabs.addTab(tools_tab, tr("external_tools"))

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton(tr("ok"))
        ok_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton(tr("cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load settings from storage."""
        # Language
        current_lang = self.settings.get_language()
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        self.dark_mode_check.setChecked(self.settings.get_dark_mode())
        self.text_ext_edit.setPlainText(self.settings.get_text_extensions())
        self.image_ext_edit.setPlainText(self.settings.get_image_extensions())

        self.text_threshold_spin.setValue(int(self.settings.get_text_similarity_threshold()))
        self.image_threshold_spin.setValue(int(self.settings.get_image_similarity_threshold()))
        self.binary_threshold_spin.setValue(int(self.settings.get_binary_similarity_threshold()))

        self.text_tool_widget.load_config(self.settings.get_external_tool_config("text"))
        self.image_tool_widget.load_config(self.settings.get_external_tool_config("image"))
        self.binary_tool_widget.load_config(self.settings.get_external_tool_config("binary"))

    def _save_and_close(self):
        """Save settings and close dialog."""
        # Language
        old_lang = self.settings.get_language()
        selected_lang = self.language_combo.currentData()
        self.settings.set_language(selected_lang)

        # Emit signal if language changed
        if old_lang != selected_lang:
            self.language_changed.emit()

        self.settings.set_dark_mode(self.dark_mode_check.isChecked())
        self.settings.set_text_extensions(self.text_ext_edit.toPlainText())
        self.settings.set_image_extensions(self.image_ext_edit.toPlainText())

        self.settings.set_text_similarity_threshold(float(self.text_threshold_spin.value()))
        self.settings.set_image_similarity_threshold(float(self.image_threshold_spin.value()))
        self.settings.set_binary_similarity_threshold(float(self.binary_threshold_spin.value()))

        self.settings.set_external_tool_config("text", self.text_tool_widget.get_config())
        self.settings.set_external_tool_config("image", self.image_tool_widget.get_config())
        self.settings.set_external_tool_config("binary", self.binary_tool_widget.get_config())

        self.accept()
