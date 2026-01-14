"""
Custom styled dialogs for better UI
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ..utils.styles import COLORS, get_button_style


class StyledInputDialog(QDialog):
    """A pretty custom input dialog"""

    def __init__(self, parent=None, title="Input", label="Enter value:", input_type="text", **kwargs):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(420)

        self.input_value = None
        self.input_type = input_type
        self.kwargs = kwargs

        self.init_ui(label)

    def init_ui(self, label_text):
        """Initialise the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

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
        """)

        # Label
        label = QLabel(label_text)
        label_font = QFont()
        label_font.setPointSize(13)
        label_font.setBold(True)
        label.setFont(label_font)
        label.setStyleSheet(f"color: #e6edf3; margin-bottom: 8px;")
        layout.addWidget(label)

        # Input widget based on type
        if self.input_type == "text":
            self.input_widget = QLineEdit()
            self.input_widget.setText(self.kwargs.get('default', ''))
            self.input_widget.setPlaceholderText(self.kwargs.get('placeholder', ''))
            self.input_widget.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {COLORS['bg_primary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_primary']};
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }}
                QLineEdit:focus {{
                    border-color: {COLORS['accent_blue']};
                }}
            """)

        elif self.input_type == "int":
            self.input_widget = QSpinBox()
            self.input_widget.setMinimum(self.kwargs.get('min_val', self.kwargs.get('min', 0)))
            self.input_widget.setMaximum(self.kwargs.get('max_val', self.kwargs.get('max', 100)))
            self.input_widget.setValue(self.kwargs.get('default', 0))
            self.input_widget.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {COLORS['bg_primary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_primary']};
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }}
                QSpinBox:focus {{
                    border-color: {COLORS['accent_blue']};
                }}
                QSpinBox::up-button, QSpinBox::down-button {{
                    background-color: {COLORS['bg_tertiary']};
                    border: none;
                    width: 20px;
                }}
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                    background-color: {COLORS['bg_hover']};
                }}
            """)

        elif self.input_type == "double":
            self.input_widget = QDoubleSpinBox()
            self.input_widget.setMinimum(self.kwargs.get('min_val', self.kwargs.get('min', 0.0)))
            self.input_widget.setMaximum(self.kwargs.get('max_val', self.kwargs.get('max', 100.0)))
            self.input_widget.setValue(self.kwargs.get('default', 0.0))
            self.input_widget.setDecimals(self.kwargs.get('decimals', 1))
            self.input_widget.setSingleStep(self.kwargs.get('step', 0.1))
            self.input_widget.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background-color: {COLORS['bg_primary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_primary']};
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }}
                QDoubleSpinBox:focus {{
                    border-color: {COLORS['accent_blue']};
                }}
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                    background-color: {COLORS['bg_tertiary']};
                    border: none;
                    width: 20px;
                }}
                QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                    background-color: {COLORS['bg_hover']};
                }}
            """)

        elif self.input_type == "combo":
            self.input_widget = QComboBox()
            items = self.kwargs.get('items', [])
            self.input_widget.addItems(items)
            current_index = self.kwargs.get('current_index', 0)
            if 0 <= current_index < len(items):
                self.input_widget.setCurrentIndex(current_index)
            self.input_widget.setStyleSheet(f"""
                QComboBox {{
                    background-color: {COLORS['bg_primary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_primary']};
                    border-radius: 6px;
                    padding: 10px;
                    font-size: 13px;
                }}
                QComboBox:focus {{
                    border-color: {COLORS['accent_blue']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    padding-right: 10px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border-left: 4px solid transparent;
                    border-right: 4px solid transparent;
                    border-top: 6px solid {COLORS['text_secondary']};
                    margin-right: 8px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {COLORS['bg_tertiary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_primary']};
                    selection-background-color: {COLORS['accent_blue']};
                    outline: none;
                    padding: 4px;
                }}
            """)

        layout.addWidget(self.input_widget)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(get_button_style('grey', 'medium'))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(get_button_style('blue', 'medium'))
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def get_value(self):
        """Get the input value"""
        if self.input_type == "text":
            return self.input_widget.text()
        elif self.input_type in ["int", "double"]:
            return self.input_widget.value()
        elif self.input_type == "combo":
            return self.input_widget.currentText()
        return None

    @staticmethod
    def get_text(parent=None, title="Input", label="Enter text:", default="", placeholder=""):
        """Static method to get text input"""
        dialog = StyledInputDialog(parent, title, label, "text", default=default, placeholder=placeholder)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_value(), True
        return default, False

    @staticmethod
    def get_int(parent=None, title="Input", label="Enter number:", default=0, min_val=0, max_val=100):
        """Static method to get integer input"""
        dialog = StyledInputDialog(parent, title, label, "int", default=default, min=min_val, max=max_val)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_value(), True
        return default, False

    @staticmethod
    def get_double(parent=None, title="Input", label="Enter value:", default=0.0, min_val=0.0, max_val=100.0, decimals=1, step=0.1):
        """Static method to get double input"""
        dialog = StyledInputDialog(parent, title, label, "double", default=default, min=min_val, max=max_val, decimals=decimals, step=step)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_value(), True
        return default, False

    @staticmethod
    def get_item(parent=None, title="Select", label="Choose an option:", items=[], current_index=0):
        """Static method to get item from list"""
        dialog = StyledInputDialog(parent, title, label, "combo", items=items, current_index=current_index)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_value(), True
        return items[current_index] if items else "", False
