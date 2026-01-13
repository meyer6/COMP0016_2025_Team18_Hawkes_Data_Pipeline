"""
Progress dialog for video processing
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ..utils.styles import COLORS, get_button_style, show_yes_no_dialog


class ProcessingProgressDialog(QDialog):
    """Dialog showing progress of video processing"""

    cancel_requested = pyqtSignal()  # Emitted when user clicks Cancel button

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Video")
        self.setModal(False)  # Non-modal so user can interact with main window
        self.setMinimumSize(540, 240)
        self.setMaximumWidth(600)

        # Allow close button
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )

        self.is_complete = False
        self.init_ui()

    def init_ui(self):
        """Initialise the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Set modern dark background with new colours
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
                background-color: {COLORS['accent_blue']};
                border-radius: 5px;
            }}
        """)

        # Title
        title = QLabel("Processing Video")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: -0.5px;")
        layout.addWidget(title)

        # Stage label
        self.stage_label = QLabel("Initialising...")
        self.stage_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(self.stage_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Detail label (shows frame count, etc.)
        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-size: 11px;")
        layout.addWidget(self.detail_label)

        layout.addStretch()

        # Button layout - horizontal layout for side-by-side buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()  # Push buttons to the right

        # Hide button
        self.hide_btn = QPushButton("Hide")
        self.hide_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_primary']};
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
            }}
        """)
        self.hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hide_btn.clicked.connect(self.hide)
        button_layout.addWidget(self.hide_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(get_button_style('red', 'medium'))
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def update_progress(self, stage: str, current: int, total: int):
        """
        Update progress display

        Args:
            stage: Name of current processing stage
            current: Current progress value
            total: Total progress value
        """
        self.stage_label.setText(stage)
        self.progress_bar.setValue(current)

        if stage == "Complete":
            self.is_complete = True
            self.detail_label.setText("Processing complete!")
            # Hide cancel button, change Hide to Close
            self.cancel_btn.setVisible(False)
            self.hide_btn.setText("Close")
            # Auto-close after 2 seconds to give user time to see completion message
            QTimer.singleShot(2000, self.hide)
        else:
            self.detail_label.setText(f"Progress: {current}/{total}")

    def on_cancel_clicked(self):
        """Handle cancel button click"""
        self.cancel_requested.emit()

    def reset(self):
        """Reset dialog to initial state"""
        self.is_complete = False
        self.cancel_btn.setVisible(True)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self.hide_btn.setText("Hide")
        self.stage_label.setText("Initialising...")
        self.detail_label.setText("")
        self.progress_bar.setValue(0)

    def closeEvent(self, event):
        """Handle close event - allow closing (just hides the dialog)"""
        event.accept()  # Allow close (which just hides the dialog, doesn't cancel processing)
