"""Main window for difflex application."""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PySide6.QtGui import QAction

from ..utils.settings import Settings
from ..utils.i18n import tr
from .home_widget import HomeWidget
from .file_comparison_widget import FileComparisonWidget
from .parallel_comparison_widget import ParallelComparisonWidget
from .settings_dialog import SettingsDialog
from .history_dialog import HistoryDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(1000, 600)

        self.settings = Settings()
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Setup user interface."""
        # Menu bar
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu(tr("menu_file"))

        new_tab_action = QAction(tr("menu_new_comparison"), self)
        new_tab_action.triggered.connect(self._new_comparison)
        file_menu.addAction(new_tab_action)

        history_action = QAction(tr("menu_history"), self)
        history_action.triggered.connect(self._show_history)
        file_menu.addAction(history_action)

        file_menu.addSeparator()

        exit_action = QAction(tr("menu_exit"), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu(tr("menu_settings"))

        settings_action = QAction(tr("menu_settings"), self)
        settings_action.triggered.connect(self._show_settings)
        settings_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu(tr("menu_help"))

        about_action = QAction(tr("menu_about"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.setCentralWidget(self.tabs)

        # Add home tab
        self._add_home_tab()

    def _add_home_tab(self):
        """Add home tab."""
        home_widget = HomeWidget()
        home_widget.compare_requested.connect(self._start_comparison)
        home_widget.history_requested.connect(self._show_history)

        self.tabs.addTab(home_widget, tr("tab_home"))

    def _new_comparison(self):
        """Create new comparison (go to home tab)."""
        # Check if home tab exists
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tr("tab_home"):
                self.tabs.setCurrentIndex(i)
                return

        # Add new home tab
        self._add_home_tab()
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def _start_comparison(self, paths: list, is_directory: bool):
        """
        Start a new comparison.

        Args:
            paths: List of file or directory paths
            is_directory: True if comparing directories
        """
        # Add to history
        history_item = {
            "paths": paths,
            "is_directory": is_directory
        }
        self.settings.add_to_history(history_item)

        # Create comparison widget based on type
        if is_directory:
            comparison_widget = ParallelComparisonWidget(paths, self.settings)
        else:
            comparison_widget = FileComparisonWidget(paths, self.settings)

        # Create tab title
        from pathlib import Path
        names = [Path(p).name for p in paths[:2]]
        title = f"{names[0]} vs {names[1]}"
        if len(paths) > 2:
            title += "..."

        # Add tab
        index = self.tabs.addTab(comparison_widget, title)
        self.tabs.setCurrentIndex(index)

    def _close_tab(self, index: int):
        """Close a tab."""
        # Don't close if it's the last tab
        if self.tabs.count() <= 1:
            return

        # Don't close home tab if there are other tabs
        if self.tabs.tabText(index) == tr("tab_home") and self.tabs.count() > 1:
            # Check if there are other home tabs
            home_count = sum(1 for i in range(self.tabs.count()) if self.tabs.tabText(i) == tr("tab_home"))
            if home_count <= 1:
                return

        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget:
            widget.deleteLater()

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.language_changed.connect(self._on_language_changed)
        if dialog.exec():
            self._apply_theme()

    def _on_language_changed(self):
        """Handle language change by showing restart message."""
        QMessageBox.information(
            self,
            tr("language_changed_title"),
            tr("language_changed_message")
        )

    def _show_history(self):
        """Show history dialog."""
        dialog = HistoryDialog(self)
        dialog.compare_requested.connect(self._start_comparison)
        dialog.exec()

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            tr("about_title"),
            tr("about_text")
        )

    def _apply_theme(self):
        """Apply theme based on settings."""
        dark_mode = self.settings.get_dark_mode()

        if dark_mode:
            self.setStyleSheet("""
                QMainWindow, QDialog, QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTableWidget {
                    background-color: #3c3c3c;
                    alternate-background-color: #404040;
                    gridline-color: #555555;
                }
                QHeaderView::section {
                    background-color: #505050;
                    color: #ffffff;
                    padding: 5px;
                    border: 1px solid #666666;
                }
                QPushButton {
                    background-color: #505050;
                    color: #ffffff;
                    border: 1px solid #666666;
                    padding: 5px 15px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #606060;
                }
                QPushButton:pressed {
                    background-color: #404040;
                }
                QPushButton:disabled {
                    background-color: #3c3c3c;
                    color: #888888;
                }
                QLineEdit, QTextEdit, QSpinBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #666666;
                    padding: 3px;
                }
                QGroupBox {
                    border: 1px solid #666666;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    color: #ffffff;
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    padding: 0 5px;
                }
                QTabWidget::pane {
                    border: 1px solid #666666;
                    background-color: #2b2b2b;
                }
                QTabBar::tab {
                    background-color: #505050;
                    color: #ffffff;
                    padding: 5px 10px;
                    border: 1px solid #666666;
                }
                QTabBar::tab:selected {
                    background-color: #2b2b2b;
                }
                QProgressBar {
                    border: 1px solid #666666;
                    border-radius: 3px;
                    text-align: center;
                    background-color: #3c3c3c;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #505050;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                    border: 1px solid #666666;
                }
                QMenu::item:selected {
                    background-color: #505050;
                }
            """)
        else:
            self.setStyleSheet("")

    def closeEvent(self, event):
        """Handle close event."""
        # Stop all comparison workers
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, ParallelComparisonWidget) and hasattr(widget, 'worker') and widget.worker:
                widget.worker.stop()
                widget.worker.wait()

        event.accept()
