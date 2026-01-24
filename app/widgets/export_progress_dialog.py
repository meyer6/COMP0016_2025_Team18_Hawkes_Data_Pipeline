"""
Progress dialog for video export
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..utils.styles import COLORS


class ExportProgressDialog(QDialog):
    """Dialog showing progress of video export"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exporting Clips")
        self.setModal(True)
        self.setMinimumSize(540, 220)
        self.setMaximumWidth(600)

        # Disable close button during export
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        self.init_ui()

    def init_ui(self):
        """Initialise the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Set modern dark background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_primary']};
                border-radius: 12px;
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QProgressBar {{
                border: 1px solid {COLORS['border_primary']};
                border-radius: 6px;
                background-color: {COLORS['bg_primary']};
                text-align: center;
                color: {COLORS['text_primary']};
                height: 24px;
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent_green']};
                border-radius: 5px;
            }}
        """)

        # Title
        title = QLabel("Exporting Video Clips")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: -0.5px;")
        layout.addWidget(title)

        # Message label
        self.message_label = QLabel("Preparing export...")
        self.message_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(self.message_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Detail label
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-size: 11px;")
        layout.addWidget(self.detail_label)

        layout.addStretch()

    def update_progress(self, current: int, total: int, message: str):
        """
        Update progress display

        Args:
            current: Current clip number
            total: Total clips to export
            message: Current operation message
        """
        self.message_label.setText(message)

        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.detail_label.setText(f"Clip {current} of {total}")

        if current >= total and total > 0:
            self.detail_label.setText("Export complete!")
            self.accept()  # Auto-close on completion
