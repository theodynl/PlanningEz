"""Task table widget for displaying tasks in a list."""

from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from planningez.core.models import Project, Task


class TaskTableWidget(QWidget):
    """Widget for displaying tasks in a table."""

    task_clicked = Signal(str)  # task_id
    task_double_clicked = Signal(str)  # task_id
    add_task = Signal()
    edit_task = Signal(str)  # task_id
    delete_task = Signal(str)  # task_id

    def __init__(self, project: Project, parent: Optional[QWidget] = None) -> None:
        """Initialize task table.

        Args:
            project: Project to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.project = project

        self._init_ui()
        self._populate_table()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name",
            "Duration",
            "Status",
            "Progress",
            "Start",
            "End",
            "Responsible",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.itemClicked.connect(self._on_item_clicked)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()

        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_task.emit)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _populate_table(self) -> None:
        """Populate table with tasks."""
        self.table.setRowCount(0)

        for i, task in enumerate(self.project.tasks):
            self.table.insertRow(i)

            # Name
            name_item = QTableWidgetItem(task.name)
            self.table.setItem(i, 0, name_item)

            # Duration
            duration_item = QTableWidgetItem(f"{task.duration} {task.unit}")
            self.table.setItem(i, 1, duration_item)

            # Status
            status_item = QTableWidgetItem(task.status.value)
            self.table.setItem(i, 2, status_item)

            # Progress
            progress_item = QTableWidgetItem(f"{int(task.progress)}%")
            self.table.setItem(i, 3, progress_item)

            # Start date
            start_item = QTableWidgetItem(
                task.start_date.isoformat() if task.start_date else "-"
            )
            self.table.setItem(i, 4, start_item)

            # End date
            end_item = QTableWidgetItem(
                task.end_date.isoformat() if task.end_date else "-"
            )
            self.table.setItem(i, 5, end_item)

            # Responsible
            resource = (
                self.project.get_resource(task.responsible)
                if task.responsible
                else None
            )
            responsible_item = QTableWidgetItem(
                resource.name if resource else "-"
            )
            self.table.setItem(i, 6, responsible_item)

            # Store task_id in item
            name_item.setData(Qt.ItemDataRole.UserRole, task.task_id)

    def refresh(self) -> None:
        """Refresh the table."""
        self._populate_table()

    def _on_item_clicked(self, item) -> None:
        """Handle item click."""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_clicked.emit(task_id)

    def _on_item_double_clicked(self, item) -> None:
        """Handle item double click."""
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id:
            self.task_double_clicked.emit(task_id)

    def _on_edit_clicked(self) -> None:
        """Handle edit button."""
        current_item = self.table.currentItem()
        if current_item:
            task_id = current_item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.edit_task.emit(task_id)

    def _on_delete_clicked(self) -> None:
        """Handle delete button."""
        current_item = self.table.currentItem()
        if current_item:
            task_id = current_item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.delete_task.emit(task_id)

    def get_selected_task_id(self) -> Optional[str]:
        """Get the selected task ID."""
        current_item = self.table.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None
