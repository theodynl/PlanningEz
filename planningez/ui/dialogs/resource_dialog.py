"""Dialog for creating and editing resources."""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QTextEdit,
    QPushButton, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from planningez.core.models import Resource, ResourceRole


class ResourceDialog(QDialog):
    """Dialog for creating/editing resources."""

    def __init__(
        self,
        parent=None,
        resource: Optional[Resource] = None,
    ) -> None:
        """Initialize resource dialog.

        Args:
            parent: Parent widget
            resource: Resource to edit (None for new resource)
        """
        super().__init__(parent)
        self.resource = resource or Resource(name="New Resource")
        self.is_new = resource is None

        self.setWindowTitle(
            "New Resource" if self.is_new else f"Edit Resource: {self.resource.name}"
        )
        self.setMinimumWidth(400)

        self._init_ui()
        self._populate_fields()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Resource name
        self.name_input = QLineEdit()
        form.addRow("Name:", self.name_input)

        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems([r.value for r in ResourceRole])
        form.addRow("Role:", self.role_combo)

        # Company
        self.company_input = QLineEdit()
        form.addRow("Company:", self.company_input)

        # Daily cost
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMinimum(0.0)
        self.cost_input.setMaximum(10000.0)
        self.cost_input.setSuffix(" €/day")
        form.addRow("Daily Cost:", self.cost_input)

        # Availability
        self.availability_input = QDoubleSpinBox()
        self.availability_input.setMinimum(0.0)
        self.availability_input.setMaximum(100.0)
        self.availability_input.setSuffix(" %")
        form.addRow("Availability:", self.availability_input)

        # Email
        self.email_input = QLineEdit()
        form.addRow("Email:", self.email_input)

        # Phone
        self.phone_input = QLineEdit()
        form.addRow("Phone:", self.phone_input)

        # Comments
        self.comments_input = QTextEdit()
        self.comments_input.setMaximumHeight(100)
        form.addRow("Comments:", self.comments_input)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_resource)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _populate_fields(self) -> None:
        """Populate form fields with resource data."""
        self.name_input.setText(self.resource.name)
        self.role_combo.setCurrentText(self.resource.role.value)
        self.company_input.setText(self.resource.company or "")
        self.cost_input.setValue(self.resource.daily_cost)
        self.availability_input.setValue(self.resource.availability)
        self.email_input.setText(self.resource.email or "")
        self.phone_input.setText(self.resource.phone or "")
        self.comments_input.setPlainText(self.resource.comments)

    def save_resource(self) -> None:
        """Save resource changes."""
        self.resource.name = self.name_input.text()
        self.resource.role = ResourceRole(self.role_combo.currentText())
        self.resource.company = self.company_input.text() or None
        self.resource.daily_cost = self.cost_input.value()
        self.resource.availability = self.availability_input.value()
        self.resource.email = self.email_input.text() or None
        self.resource.phone = self.phone_input.text() or None
        self.resource.comments = self.comments_input.toPlainText()

        self.accept()

    def get_resource(self) -> Resource:
        """Get the edited resource."""
        return self.resource
