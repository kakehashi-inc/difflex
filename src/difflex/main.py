"""Main entry point for difflex application."""

import sys
from PySide6.QtWidgets import QApplication

from .modules.main_window import MainWindow
from .utils.i18n import init_translator
from .utils.settings import Settings


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Difflex")
    app.setOrganizationName("difflex")
    app.setApplicationVersion("0.0.1")

    # Initialize translation system
    settings = Settings()
    language = settings.get_language()
    if language:
        # Use saved language preference
        init_translator(language)
    else:
        # Auto-detect system language
        init_translator()

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
