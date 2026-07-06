"""Application stylesheets for PlanningEz."""

# Color palette
PRIMARY_DARK = "#1E4D3A"
PRIMARY_LIGHT = "#2E7D5A"
SECONDARY = "#F28C28"
TEXT_DARK = "#1F2937"
TEXT_LIGHT = "#6B7280"
BACKGROUND = "#F9FAFB"
BORDER = "#E5E7EB"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
ERROR = "#EF4444"

STYLESHEET = f"""
QMainWindow {{
    background-color: {BACKGROUND};
}}

QWidget {{
    background-color: {BACKGROUND};
    color: {TEXT_DARK};
}}

QPushButton {{
    background-color: {PRIMARY_LIGHT};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {PRIMARY_DARK};
}}

QPushButton:pressed {{
    background-color: {TEXT_DARK};
}}

QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 8px;
    background-color: white;
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 2px solid {PRIMARY_LIGHT};
}}

QComboBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 8px;
    background-color: white;
}}

QTableWidget {{
    gridline-color: {BORDER};
    background-color: white;
}}

QTableWidget::item {{
    padding: 4px;
}}

QHeaderView::section {{
    background-color: {BACKGROUND};
    color: {TEXT_DARK};
    padding: 6px;
    border: 1px solid {BORDER};
    font-weight: bold;
}}

QMenuBar {{
    background-color: white;
    color: {TEXT_DARK};
    border-bottom: 1px solid {BORDER};
}}

QMenuBar::item:selected {{
    background-color: {BACKGROUND};
}}

QMenu {{
    background-color: white;
    color: {TEXT_DARK};
    border: 1px solid {BORDER};
}}

QMenu::item:selected {{
    background-color: {BACKGROUND};
}}

QToolBar {{
    background-color: white;
    border-bottom: 1px solid {BORDER};
    spacing: 4px;
}}

QStatusBar {{
    background-color: white;
    color: {TEXT_LIGHT};
    border-top: 1px solid {BORDER};
}}

QLabel {{
    color: {TEXT_DARK};
}}

QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
}}
"""

def get_stylesheet() -> str:
    """Get the application stylesheet."""
    return STYLESHEET
