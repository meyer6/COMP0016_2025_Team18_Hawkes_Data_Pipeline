"""
Video editor view with playback and annotation editing
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSlider, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from pathlib import Path

from ..widgets.timeline_widget import TimelineWidget
from ..widgets.custom_dialogs import StyledInputDialog
from ..utils.styles import COLORS, get_button_style, show_info_dialog, show_error_dialog, show_warning_dialog, show_yes_no_dialog


class VideoEditorView(QWidget):
    """Video editor view with playback and timeline"""

    back_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    export_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self.annotation = None
        self.duration = 0
        self.has_unsaved_changes = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        header = self.create_header()
        layout.addWidget(header)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #000;")
        layout.addWidget(self.video_widget, stretch=1)

        controls = self.create_controls()
        layout.addWidget(controls)

        timeline_container = QWidget()
        timeline_container.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-top: 1px solid {COLORS['border_primary']};")
        timeline_container.setFixedHeight(155)
        timeline_layout = QVBoxLayout(timeline_container)
        timeline_layout.setContentsMargins(0, 8, 0, 5)

        self.timeline_widget = TimelineWidget()
        self.timeline_widget.setStyleSheet(f"background-color: {COLORS['bg_secondary']};")
        self.timeline_widget.position_changed.connect(self.on_timeline_clicked)
        self.timeline_widget.segments_modified.connect(self.on_segments_modified)
        timeline_layout.addWidget(self.timeline_widget)

        layout.addWidget(timeline_container)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)

    def create_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border_primary']};")
        header.setFixedHeight(64)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(32, 16, 32, 16)

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent_blue']};
                border: 1px solid {COLORS['accent_blue']};
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue']};
                color: white;
            }}
        """)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)

        self.title_label = QLabel("Video Editor")
        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']}; margin-left: 16px; letter-spacing: -0.5px;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(get_button_style('green', 'medium'))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(save_btn)

        export_btn = QPushButton("Export Clips")
        export_btn.setStyleSheet(get_button_style('blue', 'medium'))
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_clicked.emit)
        layout.addWidget(export_btn)

        return header

    def create_controls(self) -> QWidget:
        controls = QWidget()
        controls.setStyleSheet(f"background-color: {COLORS['bg_secondary']};")
        controls.setFixedHeight(90)

        layout = QVBoxLayout(controls)
        layout.setContentsMargins(32, 12, 32, 12)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border_primary']};
                height: 6px;
                background: {COLORS['bg_primary']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent_blue']};
                border: 2px solid {COLORS['bg_secondary']};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['accent_blue_hover']};
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent_blue']};
                border-radius: 3px;
            }}
        """)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        layout.addWidget(self.progress_slider)

        controls_row = QHBoxLayout()

        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; font-weight: 500; font-family: monospace;")
        self.time_label.setToolTip("Keyboard shortcuts: Space=Play/Pause, Left/Right=Seek ±5s")
        controls_row.addWidget(self.time_label)

        controls_row.addStretch()

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setToolTip("Play/Pause (Space)")
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_blue_hover']};
            }}
        """)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_row.addWidget(self.play_btn)

        controls_row.addStretch()

        self.speed_btn = QPushButton("1.0x")
        self.speed_btn.setFixedWidth(60)
        self.speed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_primary']};
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.speed_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speed_btn.clicked.connect(self.change_playback_speed)
        controls_row.addWidget(self.speed_btn)

        layout.addLayout(controls_row)

        return controls

    def load_video(self, video_path: str, annotation=None):
        if hasattr(self, 'media_player') and self.media_player:
            self.media_player.stop()

        self.video_path = video_path
        self.annotation = annotation
        self.has_unsaved_changes = False

        filename = Path(video_path).name
        self.title_label.setText(filename)

        if not Path(video_path).exists():
            from PyQt6.QtWidgets import QMessageBox
            show_error_dialog(
                self,
                "File Not Found",
                f"Video file not found:\n{video_path}"
            )
            return

        self.media_player.setSource(QUrl.fromLocalFile(video_path))

        if annotation:
            self.timeline_widget.set_annotation(annotation, annotation.duration)

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")

    def change_playback_speed(self):
        speeds = ["0.25x", "0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "1.75x", "2.0x"]
        speed_values = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

        current_speed = self.media_player.playbackRate()
        try:
            current_index = speed_values.index(current_speed)
        except ValueError:
            current_index = 3  # Default to 1.0x

        selected_speed, ok = StyledInputDialog.get_item(
            self,
            "Playback Speed",
            "Select playback speed:",
            speeds,
            current_index
        )

        if ok:
            speed_index = speeds.index(selected_speed)
            new_speed = speed_values[speed_index]
            self.media_player.setPlaybackRate(new_speed)
            self.speed_btn.setText(selected_speed)

    def on_position_changed(self, position: int):
        self.progress_slider.setValue(position)

        current_time = self.format_time(position)
        total_time = self.format_time(self.duration)
        self.time_label.setText(f"{current_time} / {total_time}")

        position_seconds = position / 1000.0
        self.timeline_widget.set_position(position_seconds)

    def on_duration_changed(self, duration: int):
        self.duration = duration
        self.progress_slider.setRange(0, duration)

    def on_slider_moved(self, position: int):
        self.media_player.setPosition(position)

    def on_slider_pressed(self):
        position = self.progress_slider.value()
        self.media_player.setPosition(position)

    def on_timeline_clicked(self, time_seconds: float):
        position_ms = int(time_seconds * 1000)
        self.media_player.setPosition(position_ms)

    def on_segments_modified(self):
        if self.annotation:
            self.has_unsaved_changes = True
            filename = Path(self.video_path).name
            self.title_label.setText(f"{filename} *")

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")

    def format_time(self, ms: int) -> str:
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_playback()
        elif event.key() == Qt.Key.Key_Left:
            # Seek backward 5 seconds
            current = self.media_player.position()
            self.media_player.setPosition(max(0, current - 5000))
        elif event.key() == Qt.Key.Key_Right:
            # Seek forward 5 seconds
            current = self.media_player.position()
            self.media_player.setPosition(min(self.duration, current + 5000))
        super().keyPressEvent(event)

    def cleanup(self):
        if hasattr(self, 'media_player') and self.media_player:
            self.media_player.stop()
            self.media_player.setSource(QUrl())  # Clear source
            self.media_player.deleteLater()
            self.media_player = None

        if hasattr(self, 'audio_output') and self.audio_output:
            self.audio_output.deleteLater()
            self.audio_output = None
