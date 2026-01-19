"""
Dialog for selecting videos to delete
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from pathlib import Path

from ..utils.styles import COLORS, get_button_style, show_warning_dialog


class VideoDeletionDialog(QDialog):
    """Dialog for selecting which videos to delete"""

    def __init__(self, video_items, parent=None):
        """
        Initialise video deletion dialog

        Args:
            video_items: List of VideoItem objects
            parent: Parent widget
        """
        super().__init__(parent)
        self.video_items = video_items
        self.selected_videos = []
        self.checkboxes = []

        self.setWindowTitle("Delete Videos")
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
                border-color: {COLORS['accent_red']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent_red']};
                border-color: {COLORS['accent_red']};
            }}
        """)

        # Title
        title = QLabel("Select Videos to Delete")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: -0.5px;")
        layout.addWidget(title)

        # Subtitle
        if not self.video_items:
            subtitle = QLabel("No videos available.")
            subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
            layout.addWidget(subtitle)
        else:
            subtitle = QLabel(f"{len(self.video_items)} video(s) in library")
            subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
            layout.addWidget(subtitle)

            # Warning message
            warning = QLabel("⚠️ This will permanently delete thumbnails and annotations")
            warning.setStyleSheet(f"color: {COLORS['accent_red']}; font-size: 12px; padding: 8px; background-color: {COLORS['bg_primary']}; border-radius: 4px;")
            layout.addWidget(warning)

            # Select/Deselect all buttons
            select_buttons = QHBoxLayout()

            select_all_btn = QPushButton("Select All")
            select_all_btn.setStyleSheet(f"""
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

            # Add checkbox for each video
            for video_item in self.video_items:
                checkbox = QCheckBox(Path(video_item.video_path).name)
                checkbox.setChecked(False)  # Default: none selected
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
        cancel_btn.setStyleSheet(get_button_style('blue', 'medium'))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        if self.video_items:
            delete_btn = QPushButton("Delete Selected")
            delete_btn.setStyleSheet(get_button_style('red', 'medium'))
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(self.accept_deletion)
            button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

    def select_all(self):
        """Select all checkboxes"""
        for checkbox, _ in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all(self):
        """Deselect all checkboxes"""
        for checkbox, _ in self.checkboxes:
            checkbox.setChecked(False)

    def accept_deletion(self):
        """Accept dialog and save selected videos"""
        self.selected_videos = [
            video_item for checkbox, video_item in self.checkboxes
            if checkbox.isChecked()
        ]

        if not self.selected_videos:
            show_warning_dialog(
                self,
                "No Videos Selected",
                "Please select at least one video to delete."
            )
            return

        self.accept()

    def get_selected_videos(self):
        """Get list of selected video items"""
        return self.selected_videos
