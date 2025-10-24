"""Main entry point for difflex application."""

import sys
from PySide6.QtWidgets import QApplication

from .modules.main_window import MainWindow


def main():
    """Main entry point."""
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("Difflex")
    app.setOrganizationName("difflex")
    app.setApplicationVersion("0.0.1")

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
