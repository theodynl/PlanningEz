"""Gantt chart widget for visualizing project timeline."""

import logging
from datetime import date, timedelta
from typing import Optional, Tuple, Dict, List

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel
from PySide6.QtCore import Qt, QSize, QDate, QRect, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QIcon

from planningez.core.models import Project, Task
from planningez.core.services import PlanningEngine

logger = logging.getLogger(__name__)

# Color palette
COLOR_TASK = QColor("#2E7D5A")
COLOR_MILESTONE = QColor("#F28C28")
COLOR_CRITICAL = QColor("#DC2626")
COLOR_TODAY = QColor("#3B82F6")
COLOR_WEEKEND = QColor("#F3F4F6")
COLOR_BORDER = QColor("#E5E7EB")


class GanttChart(QWidget):
    """Gantt chart widget for project visualization."""

    task_clicked = Signal(str)  # task_id
    task_double_clicked = Signal(str)  # task_id

    def __init__(self, project: Project, parent: Optional[QWidget] = None) -> None:
        """Initialize Gantt chart.

        Args:
            project: Project to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.project = project
        self.engine = PlanningEngine(project)
        self.engine.calculate()

        # Chart parameters
        self.chart_start_date = project.start_date or date.today()
        self.chart_end_date = project.target_end_date or (self.chart_start_date + timedelta(days=90))
        self.day_width = 20  # pixels per day
        self.row_height = 30  # pixels per task
        self.header_height = 50
        self.left_margin = 200  # space for task names
        self.top_margin = self.header_height

        self.setMinimumSize(800, 400)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event) -> None:
        """Paint the Gantt chart."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), QColor("white"))

        # Draw header (timeline)
        self._draw_header(painter)

        # Draw tasks
        self._draw_tasks(painter)

        # Draw today line
        self._draw_today_line(painter)

    def _draw_header(self, painter: QPainter) -> None:
        """Draw chart header with dates."""
        painter.save()

        # Draw header background
        header_rect = QRect(0, 0, self.width(), self.header_height)
        painter.fillRect(header_rect, QColor("#F9FAFB"))

        # Draw timeline
        current_date = self.chart_start_date
        x = self.left_margin

        while current_date <= self.chart_end_date:
            # Vertical line
            painter.setPen(QPen(COLOR_BORDER, 1))
            painter.drawLine(x, 0, x, self.height())

            # Date text (every week)
            if current_date.weekday() == 0:  # Monday
                painter.setFont(QFont("Arial", 9))
                painter.setPen(Qt.GlobalColor.black)
                text = current_date.strftime("%b %d")
                painter.drawText(
                    QRect(x - 40, self.top_margin - 30, 80, 25),
                    Qt.AlignmentFlag.AlignCenter,
                    text,
                )

            current_date += timedelta(days=1)
            x += self.day_width

    def _draw_tasks(self, painter: QPainter) -> None:
        """Draw all tasks in the chart."""
        y = self.top_margin

        for task in self.project.tasks:
            self._draw_task(painter, task, y)
            y += self.row_height

    def _draw_task(self, painter: QPainter, task: Task, y: int) -> None:
        """Draw a single task bar.

        Args:
            painter: QPainter instance
            task: Task to draw
            y: Y position
        """
        if not task.start_date or not task.end_date:
            return

        # Calculate positions
        start_offset = (task.start_date - self.chart_start_date).days
        duration = (task.end_date - task.start_date).days + 1
        x = self.left_margin + start_offset * self.day_width
        width = max(duration * self.day_width, 10)
        height = self.row_height - 4

        # Draw background
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)

        # Choose color based on task state
        if task.on_critical_path:
            color = COLOR_CRITICAL
        else:
            try:
                color = QColor(task.color)
            except:
                color = COLOR_TASK

        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(QRect(x, y + 2, width, height), 3, 3)

        # Draw text (task name if space allows)
        if width > 50:
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(
                QRect(x + 5, y + 2, width - 10, height),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                task.name,
            )

        # Draw percentage bar
        if task.progress > 0:
            progress_width = max(width * (task.progress / 100.0), 2)
            painter.setBrush(QBrush(color.darker(120)))
            painter.drawRect(x, y + 2, progress_width, height)

        painter.restore()

    def _draw_today_line(self, painter: QPainter) -> None:
        """Draw a vertical line at today's date."""
        painter.save()

        today = date.today()
        if self.chart_start_date <= today <= self.chart_end_date:
            offset = (today - self.chart_start_date).days
            x = self.left_margin + offset * self.day_width

            painter.setPen(QPen(COLOR_TODAY, 2))
            painter.drawLine(x, self.top_margin, x, self.height())

        painter.restore()

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            task_id = self._get_task_at(event.position().toPoint())
            if task_id:
                self.task_clicked.emit(task_id)

    def mouseDoubleClickEvent(self, event) -> None:
        """Handle double click."""
        if event.button() == Qt.MouseButton.LeftButton:
            task_id = self._get_task_at(event.position().toPoint())
            if task_id:
                self.task_double_clicked.emit(task_id)

    def _get_task_at(self, pos) -> Optional[str]:
        """Get task ID at position."""
        if pos.x() < self.left_margin or pos.y() < self.top_margin:
            return None

        row = (pos.y() - self.top_margin) // self.row_height
        if 0 <= row < len(self.project.tasks):
            return self.project.tasks[row].task_id

        return None

    def set_date_range(self, start: date, end: date) -> None:
        """Set the date range to display."""
        self.chart_start_date = start
        self.chart_end_date = end
        self.update()

    def zoom_in(self) -> None:
        """Zoom in the chart."""
        self.day_width = min(self.day_width + 5, 50)
        self.update()

    def zoom_out(self) -> None:
        """Zoom out the chart."""
        self.day_width = max(self.day_width - 5, 5)
        self.update()

    def sizeHint(self) -> QSize:
        """Return recommended size."""
        width = self.left_margin + int(
            (self.chart_end_date - self.chart_start_date).days * self.day_width
        )
        height = self.top_margin + len(self.project.tasks) * self.row_height
        return QSize(width, height)
