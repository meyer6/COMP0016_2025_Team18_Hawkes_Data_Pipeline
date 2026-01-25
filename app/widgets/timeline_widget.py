"""
Timeline widget for displaying and editing video annotations
"""

from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from typing import Optional

from ..models.annotation import TaskSegment, ParticipantMarker
from .custom_dialogs import StyledInputDialog
from ..core.config import TaskColors

from ..utils.styles import show_info_dialog, show_error_dialog, show_warning_dialog, show_yes_no_dialog


class TimelineWidget(QWidget):
    """Widget for displaying video timeline with task segments and participant markers"""

    position_changed = pyqtSignal(float)  # Emits time in seconds when clicked
    segments_modified = pyqtSignal()  # Emits when segments are edited

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setMouseTracking(True)

        # Data
        self.annotation = None
        self.duration = 0.0  # Video duration in seconds
        self.current_position = 0.0  # Current playback position in seconds

        # UI state
        self.hover_time = None
        self.selected_segment_index = None

        # Drag state for segments
        self.dragging = False
        self.drag_segment_index = None
        self.drag_edge = None  # 'start' or 'end'
        self.hover_handle = None  # Tuple of (segment_index, edge) or None

        # Drag state for participant markers
        self.dragging_marker = False
        self.drag_marker_index = None
        self.hover_marker_index = None

        # Handle size in pixels
        self.handle_width = 4

    def set_annotation(self, annotation, duration: float):
        """Set the annotation data to display"""
        self.annotation = annotation
        self.duration = duration
        self.update()

    def set_position(self, position_seconds: float):
        """Update current playback position"""
        self.current_position = position_seconds
        self.update()

    def paintEvent(self, event):
        """Draw the timeline"""
        if not self.annotation or self.duration == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw timeline components
        self.draw_task_segments(painter)
        self.draw_handles(painter)
        self.draw_participant_markers(painter)
        self.draw_playhead(painter)
        self.draw_time_labels(painter)

    def draw_task_segments(self, painter: QPainter):
        """Draw colour-coded task segments"""
        timeline_rect = self.get_timeline_rect()

        for i, segment in enumerate(self.annotation.task_segments):
            # Calculate segment position
            start_x = self.time_to_x(segment.start_time, timeline_rect)
            end_x = self.time_to_x(segment.end_time, timeline_rect)
            width = end_x - start_x

            # Get colour for this task
            color = TaskColors.get_color(segment.task_name)

            # Highlight if selected
            if i == self.selected_segment_index:
                color = color.lighter(130)

            # Draw segment rectangle
            painter.fillRect(
                int(start_x),
                int(timeline_rect.top()),
                int(width),
                int(timeline_rect.height()),
                color
            )

            # Draw segment border
            painter.setPen(QPen(QColor('#222222'), 1))
            painter.drawRect(
                int(start_x),
                int(timeline_rect.top()),
                int(width),
                int(timeline_rect.height())
            )

            # Draw task label if segment is wide enough
            if width > 60:
                painter.setPen(QPen(Qt.GlobalColor.white))
                font = QFont()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)

                text_rect = QRectF(start_x, timeline_rect.top(), width, timeline_rect.height())
                painter.drawText(
                    text_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    segment.task_name.replace('_', ' ').title()
                )

    def draw_handles(self, painter: QPainter):
        """Draw resize handles on segment edges"""
        timeline_rect = self.get_timeline_rect()

        for i, segment in enumerate(self.annotation.task_segments):
            # Calculate segment edges
            start_x = self.time_to_x(segment.start_time, timeline_rect)
            end_x = self.time_to_x(segment.end_time, timeline_rect)

            # Determine if handles should be highlighted
            is_hover = self.hover_handle and self.hover_handle[0] == i
            is_dragging = self.dragging and self.drag_segment_index == i

            # Draw start handle
            start_hover = is_hover and self.hover_handle[1] == 'start'
            start_dragging = is_dragging and self.drag_edge == 'start'
            self.draw_handle(painter, start_x, timeline_rect, start_hover or start_dragging)

            # Draw end handle
            end_hover = is_hover and self.hover_handle[1] == 'end'
            end_dragging = is_dragging and self.drag_edge == 'end'
            self.draw_handle(painter, end_x, timeline_rect, end_hover or end_dragging)

    def draw_handle(self, painter: QPainter, x: float, timeline_rect: QRectF, highlighted: bool):
        """Draw a single resize handle"""
        # Choose colour based on state
        if highlighted:
            color = QColor('#2f81f7')  # Bright blue when hovered/dragged
        else:
            color = QColor('#e6edf3')  # Light grey normally

        # Draw handle rectangle with rounded corners
        handle_rect = QRectF(
            x - self.handle_width / 2,
            timeline_rect.top() + 2,
            self.handle_width,
            timeline_rect.height() - 4
        )

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor('#0d1117'), 1))
        painter.drawRoundedRect(handle_rect, 2, 2)

    def draw_participant_markers(self, painter: QPainter):
        """Draw participant markers on timeline"""
        timeline_rect = self.get_timeline_rect()
        marker_y = timeline_rect.top() - 20

        for i, marker in enumerate(self.annotation.participant_markers):
            x = self.time_to_x(marker.timestamp, timeline_rect)

            # Check if this marker is being hovered or dragged
            is_hovered = (self.hover_marker_index == i)
            is_dragged = (self.dragging_marker and self.drag_marker_index == i)

            # Draw marker triangle
            path = QPainterPath()
            path.moveTo(x, marker_y)
            path.lineTo(x - 10, marker_y - 18)
            path.lineTo(x + 10, marker_y - 18)
            path.closeSubpath()

            # Colour based on type with hover/drag effect
            if marker.participant_type == 'P':
                base_color = QColor('#2f81f7')  # Blue for participant
            else:
                base_color = QColor('#d29922')  # Orange for expert

            # Lighten if hovered or dragged
            if is_hovered or is_dragged:
                marker_color = base_color.lighter(120)
            else:
                marker_color = base_color

            # Set brush and pen, then draw once
            painter.setBrush(QBrush(marker_color))
            painter.setPen(QPen(QColor('#0d1117'), 2))
            painter.drawPath(path)

            # Draw participant number
            painter.setPen(QPen(Qt.GlobalColor.white))
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)

            text_rect = QRectF(x - 25, marker_y - 35, 50, 18)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignCenter,
                marker.label
            )

    def draw_playhead(self, painter: QPainter):
        """Draw current position playhead"""
        timeline_rect = self.get_timeline_rect()
        x = self.time_to_x(self.current_position, timeline_rect)

        # Draw playhead line with antialiasing for better centering
        pen = QPen(QColor('#FF0000'), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(
            QPointF(x, timeline_rect.top() - 30),
            QPointF(x, timeline_rect.bottom())
        )

        # Draw playhead triangle at top
        path = QPainterPath()
        path.moveTo(x, timeline_rect.top() - 10)
        path.lineTo(x - 6, timeline_rect.top() - 25)
        path.lineTo(x + 6, timeline_rect.top() - 25)
        path.closeSubpath()

        painter.fillPath(path, QBrush(QColor('#FF0000')))

    def draw_time_labels(self, painter: QPainter):
        """Draw time labels at bottom"""
        timeline_rect = self.get_timeline_rect()
        label_y = timeline_rect.bottom() + 12

        painter.setPen(QPen(QColor('#999999')))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        # Draw labels at intervals
        num_labels = 10
        for i in range(num_labels + 1):
            time_sec = (self.duration / num_labels) * i
            x = self.time_to_x(time_sec, timeline_rect)

            # Format time
            minutes = int(time_sec // 60)
            seconds = int(time_sec % 60)
            label = f"{minutes}:{seconds:02d}"

            # Draw label
            painter.drawText(
                QRectF(x - 30, label_y, 60, 20),
                Qt.AlignmentFlag.AlignCenter,
                label
            )

    def get_timeline_rect(self) -> QRectF:
        """Get the rectangle for the main timeline area"""
        margin = 40
        top_margin = 60
        bottom_margin = 20
        # Make the task bar shorter
        task_bar_height = 50

        return QRectF(
            margin,
            top_margin,
            self.width() - 2 * margin,
            task_bar_height
        )

    def time_to_x(self, time_seconds: float, timeline_rect: QRectF) -> float:
        """Convert time in seconds to x coordinate"""
        if self.duration == 0:
            return timeline_rect.left()

        ratio = time_seconds / self.duration
        return timeline_rect.left() + ratio * timeline_rect.width()

    def x_to_time(self, x: float, timeline_rect: QRectF) -> float:
        """Convert x coordinate to time in seconds"""
        if timeline_rect.width() == 0:
            return 0

        ratio = (x - timeline_rect.left()) / timeline_rect.width()
        return max(0, min(self.duration, ratio * self.duration))

    def get_handle_at_position(self, x: float, y: float) -> Optional[tuple]:
        """
        Check if position is over a resize handle

        Returns:
            Tuple of (segment_index, edge) where edge is 'start' or 'end', or None
        """
        if not self.annotation:
            return None

        timeline_rect = self.get_timeline_rect()

        # Check if y is within timeline bounds
        if not (timeline_rect.top() <= y <= timeline_rect.bottom()):
            return None

        # Hit area is larger than visual handle for easier interaction
        hit_area = 8

        # Check each segment's handles
        for i, segment in enumerate(self.annotation.task_segments):
            start_x = self.time_to_x(segment.start_time, timeline_rect)
            end_x = self.time_to_x(segment.end_time, timeline_rect)

            # Check start handle
            if abs(x - start_x) <= hit_area:
                return (i, 'start')

            # Check end handle
            if abs(x - end_x) <= hit_area:
                return (i, 'end')

        return None

    def get_segment_at_position(self, x: float, y: float) -> Optional[int]:
        """
        Check if position is over a segment

        Returns:
            Segment index or None
        """
        if not self.annotation:
            return None

        timeline_rect = self.get_timeline_rect()

        # Check if y is within timeline bounds
        if not (timeline_rect.top() <= y <= timeline_rect.bottom()):
            return None

        # Convert x to time
        time_seconds = self.x_to_time(x, timeline_rect)

        # Find segment containing this time
        for i, segment in enumerate(self.annotation.task_segments):
            if segment.start_time <= time_seconds <= segment.end_time:
                return i

        return None

    def get_participant_at_position(self, x: float, y: float) -> Optional[int]:
        """
        Check if position is over a participant marker

        Returns:
            Marker index or None
        """
        if not self.annotation:
            return None

        timeline_rect = self.get_timeline_rect()
        marker_y = timeline_rect.top() - 20

        # Check if y is in marker area
        if not (marker_y - 30 <= y <= marker_y):
            return None

        # Check each marker
        for i, marker in enumerate(self.annotation.participant_markers):
            marker_x = self.time_to_x(marker.timestamp, timeline_rect)

            # Check if x is within marker triangle (±8 pixels)
            if abs(x - marker_x) <= 8:
                return i

        return None

    def mousePressEvent(self, event):
        """Handle mouse click on timeline"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on a participant marker first
            marker_index = self.get_participant_at_position(event.pos().x(), event.pos().y())

            if marker_index is not None:
                # Start dragging marker
                self.dragging_marker = True
                self.drag_marker_index = marker_index
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return

            # Check if clicking on a handle
            handle = self.get_handle_at_position(event.pos().x(), event.pos().y())

            if handle:
                # Start dragging
                self.dragging = True
                self.drag_segment_index, self.drag_edge = handle
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                # Not on a handle, try to seek video
                timeline_rect = self.get_timeline_rect()
                if timeline_rect.contains(QPointF(event.pos())):
                    # Convert click position to time
                    time_seconds = self.x_to_time(event.pos().x(), timeline_rect)
                    self.position_changed.emit(time_seconds)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse hover and dragging"""
        timeline_rect = self.get_timeline_rect()

        if self.dragging_marker:
            # Update marker timestamp while dragging
            new_time = self.x_to_time(event.pos().x(), timeline_rect)
            if 0 <= self.drag_marker_index < len(self.annotation.participant_markers):
                marker = self.annotation.participant_markers[self.drag_marker_index]
                marker.timestamp = max(0.0, min(self.duration, new_time))
                self.update()

        elif self.dragging:
            # Update segment boundary while dragging
            new_time = self.x_to_time(event.pos().x(), timeline_rect)

            # Validate segment index
            if not (0 <= self.drag_segment_index < len(self.annotation.task_segments)):
                return

            segment = self.annotation.task_segments[self.drag_segment_index]

            # Minimum segment duration to prevent zero-duration segments
            MIN_DURATION = 0.5  # 0.5 seconds minimum

            if self.drag_edge == 'start':
                # Dragging start edge - ensure it doesn't go past end with minimum duration
                max_start_time = segment.end_time - MIN_DURATION
                segment.start_time = min(new_time, max_start_time)
                segment.start_time = max(0, segment.start_time)  # Don't go below 0

                # Also update previous segment's end time if it exists
                if self.drag_segment_index > 0:
                    prev_segment = self.annotation.task_segments[self.drag_segment_index - 1]
                    # Ensure previous segment also maintains minimum duration
                    if segment.start_time - prev_segment.start_time >= MIN_DURATION:
                        prev_segment.end_time = segment.start_time
                    else:
                        # Can't shrink previous segment any more, limit current segment
                        segment.start_time = prev_segment.start_time + MIN_DURATION

            else:  # drag_edge == 'end'
                # Dragging end edge - ensure it doesn't go past start with minimum duration
                min_end_time = segment.start_time + MIN_DURATION
                segment.end_time = max(new_time, min_end_time)
                segment.end_time = min(self.duration, segment.end_time)  # Don't exceed video duration

                # Also update next segment's start time if it exists
                if self.drag_segment_index < len(self.annotation.task_segments) - 1:
                    next_segment = self.annotation.task_segments[self.drag_segment_index + 1]
                    # Ensure next segment also maintains minimum duration
                    if next_segment.end_time - segment.end_time >= MIN_DURATION:
                        next_segment.start_time = segment.end_time
                    else:
                        # Can't shrink next segment any more, limit current segment
                        segment.end_time = next_segment.end_time - MIN_DURATION

            self.update()

        else:
            # Not dragging - check for marker hover
            marker_index = self.get_participant_at_position(event.pos().x(), event.pos().y())

            if marker_index is not None:
                self.hover_marker_index = marker_index
                self.hover_handle = None
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.hover_marker_index = None
                # Check for handle hover
                handle = self.get_handle_at_position(event.pos().x(), event.pos().y())

                if handle:
                    self.hover_handle = handle
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                elif timeline_rect.contains(QPointF(event.pos())):
                    self.hover_handle = None
                    self.hover_time = self.x_to_time(event.pos().x(), timeline_rect)
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    self.hover_handle = None
                    self.hover_time = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)

            self.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - finish dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging_marker:
                # Finish dragging marker
                self.dragging_marker = False
                self.drag_marker_index = None

                # Emit signal that segments were modified
                self.segments_modified.emit()

                # Update cursor based on current position
                marker_index = self.get_participant_at_position(event.pos().x(), event.pos().y())
                if marker_index is not None:
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                else:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)

                self.update()

            elif self.dragging:
                # Finish dragging segment
                self.dragging = False
                self.drag_segment_index = None
                self.drag_edge = None

                # Emit signal that segments were modified
                self.segments_modified.emit()

                # Update cursor based on current position
                handle = self.get_handle_at_position(event.pos().x(), event.pos().y())
                if handle:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)

                self.update()

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        if not self.annotation:
            return

        # Check what was clicked
        segment_index = self.get_segment_at_position(event.pos().x(), event.pos().y())
        participant_index = self.get_participant_at_position(event.pos().x(), event.pos().y())

        menu = QMenu(self)

        if segment_index is not None:
            # Context menu for segment
            segment = self.annotation.task_segments[segment_index]

            # Change task type action
            change_type_action = menu.addAction(f"Change Task Type (currently: {segment.task_name})")
            change_type_action.triggered.connect(lambda: self.change_segment_type(segment_index))

            # Split segment action
            split_action = menu.addAction("Split Segment Here")
            split_action.triggered.connect(lambda: self.split_segment(segment_index, event.pos()))

            menu.addSeparator()

            # Delete segment action
            delete_action = menu.addAction("Delete Segment")
            delete_action.triggered.connect(lambda: self.delete_segment(segment_index))

        elif participant_index is not None:
            # Context menu for participant marker
            marker = self.annotation.participant_markers[participant_index]

            # Edit participant label
            edit_label_action = menu.addAction(f"Edit Participant ({marker.label})")
            edit_label_action.triggered.connect(lambda: self.edit_participant_marker(participant_index))

            # Edit timestamp
            edit_time_action = menu.addAction("Edit Timestamp")
            edit_time_action.triggered.connect(lambda: self.edit_participant_time(participant_index))

            menu.addSeparator()

            # Delete marker
            delete_action = menu.addAction("Delete Marker")
            delete_action.triggered.connect(lambda: self.delete_participant_marker(participant_index))

        else:
            # Context menu for empty space
            add_segment_action = menu.addAction("Add New Segment Here")
            add_segment_action.triggered.connect(lambda: self.add_segment(event.pos()))

            add_marker_action = menu.addAction("Add Participant Marker Here")
            add_marker_action.triggered.connect(lambda: self.add_participant_marker(event.pos()))

        menu.exec(event.globalPos())

    def change_segment_type(self, segment_index: int):
        """Change the task type of a segment"""
        segment = self.annotation.task_segments[segment_index]

        # Get available task types
        task_types = list(TaskColors.get_all_colors().keys())

        # Show dialog
        new_type, ok = StyledInputDialog.get_item(
            self,
            "Change Task Type",
            "Select new task type:",
            task_types,
            task_types.index(segment.task_name) if segment.task_name in task_types else 0
        )

        if ok and new_type:
            segment.task_name = new_type
            self.segments_modified.emit()
            self.update()

    def split_segment(self, segment_index: int, pos):
        """Split a segment at the clicked position"""
        segment = self.annotation.task_segments[segment_index]
        timeline_rect = self.get_timeline_rect()

        # Get split time
        split_time = self.x_to_time(pos.x(), timeline_rect)

        # Minimum segment duration
        MIN_DURATION = 0.5

        # Ensure split creates two segments with minimum duration
        if (split_time - segment.start_time < MIN_DURATION or
            segment.end_time - split_time < MIN_DURATION):
            from PyQt6.QtWidgets import QMessageBox
            show_warning_dialog(
                self,
                "Cannot Split",
                f"Cannot split here: both resulting segments must be at least {MIN_DURATION} seconds long."
            )
            return

        # Ensure split is within segment
        if split_time <= segment.start_time or split_time >= segment.end_time:
            return

        # Create new segment
        new_segment = TaskSegment(
            task_name=segment.task_name,
            start_time=split_time,
            end_time=segment.end_time,
            confidence=segment.confidence
        )

        # Update original segment
        segment.end_time = split_time

        # Insert new segment
        self.annotation.task_segments.insert(segment_index + 1, new_segment)

        self.segments_modified.emit()
        self.update()

    def delete_segment(self, segment_index: int):
        """Delete a segment and merge adjacent segments if needed"""
        if len(self.annotation.task_segments) <= 1:
            # Can't delete the last segment
            from PyQt6.QtWidgets import QMessageBox
            show_warning_dialog(
                self,
                "Cannot Delete",
                "Cannot delete the last segment. At least one segment must remain."
            )
            return

        segment = self.annotation.task_segments[segment_index]

        # If there's a next segment, extend it backward
        if segment_index < len(self.annotation.task_segments) - 1:
            next_segment = self.annotation.task_segments[segment_index + 1]
            next_segment.start_time = segment.start_time
        # If there's a previous segment, extend it forward
        elif segment_index > 0:
            prev_segment = self.annotation.task_segments[segment_index - 1]
            prev_segment.end_time = segment.end_time

        # Remove segment
        self.annotation.task_segments.pop(segment_index)

        self.segments_modified.emit()
        self.update()

    def add_segment(self, pos):
        """Add a new segment at the clicked position"""
        timeline_rect = self.get_timeline_rect()
        click_time = self.x_to_time(pos.x(), timeline_rect)

        # Get task type from user
        task_types = list(TaskColors.get_all_colors().keys())
        task_type, ok = StyledInputDialog.get_item(
            self,
            "New Segment",
            "Select task type:",
            task_types,
            0
        )

        if not ok or not task_type:
            return

        # Get duration from user
        duration, ok = StyledInputDialog.get_double(
            self,
            "New Segment",
            "Segment duration (seconds):",
            default=5.0,
            min_val=0.1,
            max_val=self.duration - click_time,
            decimals=1
        )

        if not ok:
            return

        # Create new segment
        new_segment = TaskSegment(
            task_name=task_type,
            start_time=click_time,
            end_time=min(click_time + duration, self.duration),
            confidence=1.0
        )

        # Find where to insert
        insert_index = 0
        for i, seg in enumerate(self.annotation.task_segments):
            if seg.start_time < click_time:
                insert_index = i + 1
            else:
                break

        # Minimum segment duration
        MIN_DURATION = 0.5

        # Adjust adjacent segments, ensuring they maintain minimum duration
        if insert_index > 0:
            prev_segment = self.annotation.task_segments[insert_index - 1]
            # Only adjust if it won't make the previous segment too small
            if new_segment.start_time - prev_segment.start_time >= MIN_DURATION:
                prev_segment.end_time = new_segment.start_time
            else:
                # Can't fit the new segment here without breaking adjacent segments
                from PyQt6.QtWidgets import QMessageBox
                show_warning_dialog(
                    self,
                    "Cannot Add Segment",
                    "Not enough space to add a new segment here without making adjacent segments too small."
                )
                return

        if insert_index < len(self.annotation.task_segments):
            next_segment = self.annotation.task_segments[insert_index]
            # Only adjust if it won't make the next segment too small
            if next_segment.end_time - new_segment.end_time >= MIN_DURATION:
                next_segment.start_time = new_segment.end_time
            else:
                # Can't fit the new segment here without breaking adjacent segments
                from PyQt6.QtWidgets import QMessageBox
                show_warning_dialog(
                    self,
                    "Cannot Add Segment",
                    "Not enough space to add a new segment here without making adjacent segments too small."
                )
                return

        # Insert segment
        self.annotation.task_segments.insert(insert_index, new_segment)

        self.segments_modified.emit()
        self.update()

    def edit_participant_marker(self, marker_index: int):
        """Edit a participant marker's label"""
        marker = self.annotation.participant_markers[marker_index]

        # Get participant type
        types = ['P', 'E']
        p_type, ok = StyledInputDialog.get_item(
            self,
            "Edit Participant",
            "Participant type:",
            types,
            types.index(marker.participant_type)
        )

        if not ok:
            return

        # Get participant number
        number, ok = StyledInputDialog.get_int(
            self,
            "Edit Participant",
            "Participant number:",
            default=marker.participant_number,
            min_val=1,
            max_val=999
        )

        if ok:
            marker.participant_type = p_type
            marker.participant_number = number
            self.segments_modified.emit()
            self.update()

    def edit_participant_time(self, marker_index: int):
        """Edit a participant marker's timestamp"""
        marker = self.annotation.participant_markers[marker_index]

        # Get new timestamp
        new_time, ok = StyledInputDialog.get_double(
            self,
            "Edit Timestamp",
            "Timestamp (seconds):",
            default=marker.timestamp,
            min_val=0,
            max_val=self.duration,
            decimals=1
        )

        if ok:
            marker.timestamp = new_time
            self.segments_modified.emit()
            self.update()

    def delete_participant_marker(self, marker_index: int):
        """Delete a participant marker"""
        self.annotation.participant_markers.pop(marker_index)
        self.segments_modified.emit()
        self.update()

    def add_participant_marker(self, pos):
        """Add a new participant marker at the clicked position"""
        timeline_rect = self.get_timeline_rect()
        click_time = self.x_to_time(pos.x(), timeline_rect)

        # Get participant type
        types = ['P', 'E']
        p_type, ok = StyledInputDialog.get_item(
            self,
            "New Participant Marker",
            "Participant type:",
            types,
            0
        )

        if not ok:
            return

        # Get participant number
        number, ok = StyledInputDialog.get_int(
            self,
            "New Participant Marker",
            "Participant number:",
            default=1,
            min_val=1,
            max_val=999
        )

        if not ok:
            return

        # Create new marker
        new_marker = ParticipantMarker(
            participant_type=p_type,
            participant_number=number,
            timestamp=click_time,
            duration=0.0,
            confidence=1.0
        )

        # Check if a marker already exists very close to this timestamp (within 0.5 seconds)
        for marker in self.annotation.participant_markers:
            if abs(marker.timestamp - click_time) < 0.5:
                from PyQt6.QtWidgets import QMessageBox
                show_warning_dialog(
                    self,
                    "Duplicate Marker",
                    f"A participant marker already exists at {marker.timestamp:.1f}s.\n\n"
                    "Please choose a different location or edit the existing marker."
                )
                return

        # Add marker (sorted by timestamp)
        insert_index = 0
        for i, marker in enumerate(self.annotation.participant_markers):
            if marker.timestamp < click_time:
                insert_index = i + 1

        self.annotation.participant_markers.insert(insert_index, new_marker)

        self.segments_modified.emit()
        self.update()
