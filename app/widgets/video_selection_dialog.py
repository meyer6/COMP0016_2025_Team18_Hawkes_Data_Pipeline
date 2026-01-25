"""
Dialog for selecting videos to export
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path

from ..utils.styles import COLORS, get_button_style, show_warning_dialog


class VideoSelectionDialog(QDialog):
    """Dialog for selecting which videos to export"""

    def __init__(self, video_items, parent=None):
        """
        Initialise video selection dialog

        Args:
            video_items: List of VideoItem objects (only processed ones will be shown)
            parent: Parent widget
        """
        super().__init__(parent)
        self.video_items = video_items

        # Filter to only processed videos
        self.processed_videos = [v for v in video_items if v.processed]

        self.selected_videos = []
        self.checkboxes = []

        self.setWindowTitle("Select Videos to Export")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        self.init_ui()

    def init_ui(self):
        """Initialise the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(32, 32, 32, 32)

        # Set modern dark background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QCheckBox {{
                color: {COLORS['text_primary']};
                spacing: 8px;
                padding: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {COLORS['border_primary']};
                border-radius: 4px;
                background-color: {COLORS['bg_primary']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COLORS['accent_blue']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent_blue']};
                border-color: {COLORS['accent_blue']};
            }}
        """)

        # Title
        title = QLabel("Select Videos to Export")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: -0.5px;")
        layout.addWidget(title)

        # Subtitle
        if not self.processed_videos:
            subtitle = QLabel("No processed videos available to export.")
            subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
            layout.addWidget(subtitle)
        else:
            subtitle = QLabel(f"{len(self.processed_videos)} processed video(s) available")
            subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
            layout.addWidget(subtitle)

            # Select/Deselect all buttons
            select_buttons = QHBoxLayout()

            select_all_btn = QPushButton("Select All")
            select_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['accent_blue']};
                    border: 1px solid {COLORS['accent_blue']};
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_blue']};
                    color: white;
                }}
            """)
            select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            select_all_btn.clicked.connect(self.select_all)
            select_buttons.addWidget(select_all_btn)

            deselect_all_btn = QPushButton("Deselect All")
            deselect_all_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border_primary']};
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)
            deselect_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            deselect_all_btn.clicked.connect(self.deselect_all)
            select_buttons.addWidget(deselect_all_btn)

            select_buttons.addStretch()
            layout.addLayout(select_buttons)

            # Scroll area for video list
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(f"""
                QScrollArea {{
                    border: 1px solid {COLORS['border_primary']};
                    border-radius: 8px;
                    background-color: {COLORS['bg_primary']};
                }}
            """)

            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setSpacing(2)
            scroll_layout.setContentsMargins(12, 12, 12, 12)

            # Add checkbox for each processed video
            for video_item in self.processed_videos:
                checkbox = QCheckBox(Path(video_item.video_path).name)
                checkbox.setChecked(True)  # Default: all selected
                checkbox.setStyleSheet(f"""
                    QCheckBox {{
                        color: {COLORS['text_primary']};
                        font-size: 13px;
                        padding: 8px;
                        background-color: {COLORS['bg_secondary']};
                        border-radius: 4px;
                    }}
                    QCheckBox:hover {{
                        background-color: {COLORS['bg_tertiary']};
                    }}
                """)
                checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
                self.checkboxes.append((checkbox, video_item))
                scroll_layout.addWidget(checkbox)

            scroll_layout.addStretch()
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_button_style('red', 'medium'))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        if self.processed_videos:
            export_btn = QPushButton("Export Selected")
            export_btn.setStyleSheet(get_button_style('green', 'medium'))
            export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            export_btn.clicked.connect(self.accept_selection)
            button_layout.addWidget(export_btn)

        layout.addLayout(button_layout)

    def select_all(self):
        """Select all checkboxes"""
        for checkbox, _ in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all(self):
        """Deselect all checkboxes"""
        for checkbox, _ in self.checkboxes:
            checkbox.setChecked(False)

    def accept_selection(self):
        """Accept dialog and save selected videos"""
        self.selected_videos = [
            video_item for checkbox, video_item in self.checkboxes
            if checkbox.isChecked()
        ]

        if not self.selected_videos:
            show_warning_dialog(
                self,
                "No Videos Selected",
                "Please select at least one video to export."
            )
            return

        self.accept()

    def get_selected_videos(self):
        """Get list of selected video items"""
        return self.selected_videos
