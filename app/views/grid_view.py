"""
Grid view for displaying video thumbnails
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGridLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from typing import List
from .video_card import VideoCard
from ..models.video_item import VideoItem
from ..utils.styles import COLORS, get_button_style
from ..widgets.flow_layout import FlowLayout


class GridView(QWidget):
    """Grid view displaying video cards"""

    video_clicked = pyqtSignal(str)  # Emits video_path when card is clicked
    import_clicked = pyqtSignal()
    export_all_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_cards = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border_primary']};")
        header_widget.setFixedHeight(64)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(32, 16, 32, 16)
        header_layout.setSpacing(16)

        title = QLabel("Video Library")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLORS['text_primary']}; letter-spacing: -0.5px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        import_btn = QPushButton("+ Import Videos")
        import_btn.setStyleSheet(get_button_style('blue', 'medium'))
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_clicked.emit)
        header_layout.addWidget(import_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(get_button_style('red', 'medium'))
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self.delete_clicked.emit)
        header_layout.addWidget(delete_btn)

        export_all_btn = QPushButton("Export All")
        export_all_btn.setStyleSheet(get_button_style('green', 'medium'))
        export_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_all_btn.clicked.connect(self.export_all_clicked.emit)
        header_layout.addWidget(export_all_btn)

        main_layout.addWidget(header_widget)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_primary']};
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {COLORS['bg_primary']};
            }}
        """)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background-color: {COLORS['bg_primary']};")

        self.flow_layout = FlowLayout(self.grid_container, margin=32, h_spacing=24, v_spacing=24)

        self.scroll_area.setWidget(self.grid_container)
        self.content_layout.addWidget(self.scroll_area)

        main_layout.addWidget(self.content_widget)

        self.empty_widget = QWidget()
        self.empty_widget.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_label = QLabel("No videos imported yet\nClick '+ Import Videos' to get started")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"font-size: 16px; color: {COLORS['text_tertiary']}; background-color: transparent; line-height: 1.6;")
        empty_layout.addWidget(self.empty_label)

        self.content_layout.addWidget(self.empty_widget)
        self.scroll_area.hide()

    def add_video(self, video_item: VideoItem):
        if len(self.video_cards) == 0:
            self.empty_widget.hide()
            self.scroll_area.show()

        card = VideoCard(video_item.video_path)
        card.set_metadata(
            video_item.filename,
            video_item.duration_str,
            video_item.status_text,
            video_item.processed
        )

        if video_item.thumbnail_path:
            card.set_thumbnail(video_item.thumbnail_path)

        card.clicked.connect(self.video_clicked.emit)

        self.flow_layout.addWidget(card)

        self.video_cards.append(card)

    def clear_videos(self):
        for card in self.video_cards:
            self.flow_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()

        self.video_cards.clear()

        self.scroll_area.hide()
        self.empty_widget.show()

    def remove_video(self, video_path: str):
        for i, card in enumerate(self.video_cards):
            if card.video_path == video_path:
                self.flow_layout.removeWidget(card)
                card.setParent(None)
                card.deleteLater()
                self.video_cards.pop(i)

                if len(self.video_cards) == 0:
                    self.scroll_area.hide()
                    self.empty_widget.show()
                break

    def relayout_cards(self):
        pass

    def get_video_count(self) -> int:
        return len(self.video_cards)

    def wheelEvent(self, event):
        if self.scroll_area.isVisible():
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value() - event.angleDelta().y()
            )
        else:
            super().wheelEvent(event)
