"""Main entry point for PlanningEz application."""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from planningez.ui.main_window import MainWindow
from planningez.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def main() -> int:
    """Launch PlanningEz application."""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("PlanningEz")
        app.setApplicationVersion("0.1.0")

        # Set application style
        app.setStyle("Fusion")

        # Create and show main window
        window = MainWindow()
        window.show()

        logger.info("PlanningEz started successfully")
        return app.exec()

    except Exception as e:
        logger.exception("Fatal error during application startup: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
