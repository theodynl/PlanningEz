"""Dialog for creating and editing tasks."""

from typing import Optional
from datetime import date

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QDateEdit, QComboBox, QTextEdit,
    QPushButton, QFormLayout
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon

from planningez.core.models import Task, TaskType, TaskStatus, TaskPriority


class TaskDialog(QDialog):
    """Dialog for creating/editing tasks."""

    def __init__(
        self,
        parent=None,
        task: Optional[Task] = None,
    ) -> None:
        """Initialize task dialog.

        Args:
            parent: Parent widget
            task: Task to edit (None for new task)
        """
        super().__init__(parent)
        self.task = task or Task(name="New Task")
        self.is_new = task is None

        self.setWindowTitle("Task" if self.is_new else f"Edit Task: {self.task.name}")
        self.setMinimumWidth(400)

        self._init_ui()
        self._populate_fields()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Task name
        self.name_input = QLineEdit()
        form.addRow("Name:", self.name_input)

        # Duration
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setMinimum(0.0)
        self.duration_input.setMaximum(1000.0)
        self.duration_input.setValue(1.0)
        form.addRow("Duration:", self.duration_input)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems([s.value for s in TaskStatus])
        form.addRow("Status:", self.status_combo)

        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([p.value for p in TaskPriority])
        form.addRow("Priority:", self.priority_combo)

        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in TaskType])
        form.addRow("Type:", self.type_combo)

        # Start date
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        form.addRow("Start Date:", self.start_date_input)

        # Progress
        self.progress_input = QSpinBox()
        self.progress_input.setMinimum(0)
        self.progress_input.setMaximum(100)
        self.progress_input.setSuffix(" %")
        form.addRow("Progress:", self.progress_input)

        # Comments
        self.comments_input = QTextEdit()
        self.comments_input.setMaximumHeight(100)
        form.addRow("Comments:", self.comments_input)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_task)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _populate_fields(self) -> None:
        """Populate form fields with task data."""
        self.name_input.setText(self.task.name)
        self.duration_input.setValue(self.task.duration)
        self.status_combo.setCurrentText(self.task.status.value)
        self.priority_combo.setCurrentText(self.task.priority.value)
        self.type_combo.setCurrentText(self.task.task_type.value)
        self.progress_input.setValue(int(self.task.progress))
        self.comments_input.setPlainText(self.task.comments)

        if self.task.start_date:
            self.start_date_input.setDate(
                QDate(
                    self.task.start_date.year,
                    self.task.start_date.month,
                    self.task.start_date.day,
                )
            )

    def save_task(self) -> None:
        """Save task changes."""
        self.task.name = self.name_input.text()
        self.task.duration = self.duration_input.value()
        self.task.status = TaskStatus(self.status_combo.currentText())
        self.task.priority = TaskPriority(self.priority_combo.currentText())
        self.task.task_type = TaskType(self.type_combo.currentText())
        self.task.progress = float(self.progress_input.value())
        self.task.comments = self.comments_input.toPlainText()

        # Convert QDate to date
        qdate = self.start_date_input.date()
        self.task.start_date = date(qdate.year(), qdate.month(), qdate.day())

        self.accept()

    def get_task(self) -> Task:
        """Get the edited task."""
        return self.task
