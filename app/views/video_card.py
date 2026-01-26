"""
Video card widget for grid view
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPalette, QIcon, QColor

from ..utils.styles import COLORS


class VideoCard(QFrame):
    """A card widget displaying video thumbnail and metadata"""

    clicked = pyqtSignal(str)  # Emits video_path when clicked

    MIN_CARD_WIDTH = 240
    MAX_CARD_WIDTH = 360
    PREFERRED_CARD_WIDTH = 280
    THUMBNAIL_ASPECT_RATIO = 16 / 9  # Width / Height
    CARD_PADDING = 14
    THUMBNAIL_BORDER = 1

    def __init__(self, video_path: str, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.thumbnail_path = None
        self.thumbnail_pixmap = None  # Store original pixmap for resizing
        self.processed = False
        self.duration_str = "00:00:00"
        self.status_text = "Unprocessed"
        self.filename = ""
        self.hover_on_delete = False
        self.is_processing = False

        self.init_ui()

    def init_ui(self):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setLineWidth(1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMinimumWidth(self.MIN_CARD_WIDTH)
        self.setMaximumWidth(self.MAX_CARD_WIDTH)

        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.setStyleSheet(f"""
            VideoCard {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_primary']};
                border-radius: 8px;
            }}
            VideoCard:hover {{
                border: 1px solid {COLORS['accent_blue']};
                background-color: {COLORS['bg_tertiary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING, self.CARD_PADDING)

        self.thumbnail_container = QWidget()
        thumbnail_layout = QVBoxLayout(self.thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border_secondary']};
                border-radius: 6px;
                color: {COLORS['text_tertiary']};
                font-size: 11px;
            }}
        """)
        self.thumbnail_label.setText("No Thumbnail")
        thumbnail_layout.addWidget(self.thumbnail_label)

        self.status_badge = QLabel()
        self.status_badge.setParent(self.thumbnail_container)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.hide()  # Hidden by default
        self.status_badge.raise_()

        layout.addWidget(self.thumbnail_container)

        self.filename_label = QLabel()
        self.filename_label.setWordWrap(True)
        self.filename_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 14px;
            color: {COLORS['text_primary']};
            padding: 0px;
            line-height: 1.3;
        """)
        self.filename_label.setMaximumHeight(44)
        self.filename_label.setMinimumHeight(44)
        layout.addWidget(self.filename_label)

        self.info_label = QLabel()
        self.info_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_secondary']};")
        layout.addWidget(self.info_label)

        layout.addStretch()

        self._update_thumbnail_size()

    def set_thumbnail(self, thumbnail_path: str):
        self.thumbnail_path = thumbnail_path
        self.thumbnail_pixmap = QPixmap(thumbnail_path)
        if not self.thumbnail_pixmap.isNull():
            self.thumbnail_label.setText("")
            self._update_thumbnail_size()

    def _update_thumbnail_size(self):
        current_width = self.width()

        if current_width <= 100:
            current_width = self.PREFERRED_CARD_WIDTH

        available_width = current_width - (2 * self.CARD_PADDING) - (2 * self.THUMBNAIL_BORDER)

        if available_width < 100:
            available_width = self.MIN_CARD_WIDTH - (2 * self.CARD_PADDING) - (2 * self.THUMBNAIL_BORDER)

        thumbnail_width = available_width
        thumbnail_height = int(thumbnail_width / self.THUMBNAIL_ASPECT_RATIO)

        # Update thumbnail container and label size
        self.thumbnail_container.setFixedSize(thumbnail_width + (2 * self.THUMBNAIL_BORDER), thumbnail_height + (2 * self.THUMBNAIL_BORDER))
        self.thumbnail_label.setFixedSize(thumbnail_width, thumbnail_height)

        # Update status badge position (bottom-left corner)
        badge_y = thumbnail_height - 32
        self.status_badge.setGeometry(8, badge_y, 120, 26)

        # Re-scale thumbnail if we have one
        if self.thumbnail_pixmap and not self.thumbnail_pixmap.isNull():
            scaled = self.thumbnail_pixmap.scaled(
                thumbnail_width,
                thumbnail_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled)

        # Update card height based on content
        # Height = padding + thumbnail + spacing + filename + spacing + info + padding
        total_height = (
            self.CARD_PADDING * 2 +  # Top and bottom padding
            thumbnail_height + (2 * self.THUMBNAIL_BORDER) +  # Thumbnail
            12 +  # Spacing after thumbnail
            44 +  # Filename height
            12 +  # Spacing after filename
            20    # Info label height (approximate)
        )
        self.setFixedHeight(total_height)

    def set_metadata(self, filename: str, duration_str: str, status_text: str, processed: bool):
        """Set video metadata"""
        self.filename = filename
        self.duration_str = duration_str
        self.status_text = status_text
        self.processed = processed

        self.filename_label.setText(filename)
        self.info_label.setText(f"{duration_str} • {status_text}")

        # Update status badge visibility and styling
        if processed:
            self.status_badge.hide()
            self.is_processing = False
        else:
            # Show badge for unprocessed videos
            self.update_status_badge(status_text)

    def update_status(self, status_text: str):
        """Update the status text and badge"""
        self.status_text = status_text
        self.info_label.setText(f"{self.duration_str} • {status_text}")
        self.update_status_badge(status_text)

    def update_status_badge(self, status_text: str):
        """Update the status badge appearance based on status"""
        if "Processing" in status_text:
            # Show processing badge
            self.is_processing = True
            self.status_badge.setText("⏳ Processing")
            self.status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['accent_blue']};
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }}
            """)
            self.status_badge.show()
        elif "Failed" in status_text:
            # Show error badge
            self.is_processing = False
            self.status_badge.setText("❌ Failed")
            self.status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['accent_red']};
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }}
            """)
            self.status_badge.show()
        elif "Queued" in status_text or "queue" in status_text.lower():
            # Show queued badge
            self.is_processing = False
            self.status_badge.setText("⏱ Queued")
            self.status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['text_secondary']};
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }}
            """)
            self.status_badge.show()
        else:
            # Hide badge for processed videos
            self.status_badge.hide()
            self.is_processing = False

    def resizeEvent(self, event):
        """Handle resize events to update thumbnail size"""
        super().resizeEvent(event)
        self._update_thumbnail_size()

    def sizeHint(self):
        """Return preferred size for this card"""
        # Calculate preferred height based on preferred width
        thumbnail_width = self.PREFERRED_CARD_WIDTH - (2 * self.CARD_PADDING) - (2 * self.THUMBNAIL_BORDER)
        thumbnail_height = int(thumbnail_width / self.THUMBNAIL_ASPECT_RATIO)

        total_height = (
            self.CARD_PADDING * 2 +
            thumbnail_height + (2 * self.THUMBNAIL_BORDER) +
            12 +
            44 +
            12 +
            20
        )

        return QSize(self.PREFERRED_CARD_WIDTH, total_height)

    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_path)
        super().mousePressEvent(event)
