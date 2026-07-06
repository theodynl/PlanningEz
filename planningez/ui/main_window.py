"""Main application window for PlanningEz."""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self.setWindowTitle("PlanningEz - Planning Manager")
        self.setGeometry(100, 100, 1200, 800)

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Placeholder content
        welcome_label = QLabel("Welcome to PlanningEz v0.1.0")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = welcome_label.font()
        font.setPointSize(16)
        welcome_label.setFont(font)

        layout.addWidget(welcome_label)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        event.accept()
