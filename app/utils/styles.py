"""
Global styles and theming for the application
"""

# Colour palette
COLORS = {
    # Backgrounds
    'bg_primary': '#0d1117',      # Main background
    'bg_secondary': '#161b22',    # Cards, headers
    'bg_tertiary': '#21262d',     # Elevated surfaces
    'bg_hover': '#30363d',        # Hover states

    # Text
    'text_primary': '#e6edf3',
    'text_secondary': '#8b949e',
    'text_tertiary': '#6e7681',

    # Accents
    'accent_blue': '#2f81f7',
    'accent_blue_hover': '#1f6feb',
    'accent_green': '#3fb950',
    'accent_green_hover': '#2ea043',
    'accent_red': '#f85149',
    'accent_red_hover': '#da3633',
    'accent_orange': '#d29922',

    # Borders
    'border_primary': '#30363d',
    'border_secondary': '#21262d',

    # Special
    'shadow': 'rgba(0, 0, 0, 0.4)',
    'overlay': 'rgba(0, 0, 0, 0.3)',
}

# Global application stylesheet
GLOBAL_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}

/* Dialogs */
QDialog {{
    background-color: {COLORS['bg_secondary']};
}}

QLabel {{
    color: {COLORS['text_primary']};
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_secondary']};
}}

QPushButton:pressed {{
    background-color: {COLORS['border_primary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_tertiary']};
    border-color: {COLORS['border_secondary']};
}}

/* Input fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 6px;
    padding: 8px;
    selection-background-color: {COLORS['accent_blue']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent_blue']};
}}

/* ComboBox */
QComboBox {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 6px;
    padding: 8px;
    min-height: 20px;
}}

QComboBox:hover {{
    background-color: {COLORS['bg_hover']};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_primary']};
    selection-background-color: {COLORS['accent_blue']};
    outline: none;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: {COLORS['bg_primary']};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_hover']};
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_tertiary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_primary']};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_hover']};
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_tertiary']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Message boxes */
QMessageBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 8px;
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
    min-width: 350px;
    max-width: 500px;
    padding: 15px;
    margin: 8px;
    background-color: transparent;
    line-height: 1.4;
    qproperty-alignment: AlignCenter;
}}

QMessageBox QPushButton {{
    min-width: 90px;
    padding: 10px 20px;
    margin: 4px;
}}

QMessageBox QDialogButtonBox {{
    padding: 15px;
    margin-top: 5px;
}}

/* Menu and context menus */
QMenu {{
    background-color: {COLORS['bg_tertiary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent_blue']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border_primary']};
    margin: 4px 8px;
}}

/* Status bar */
QStatusBar {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border_primary']};
}}

/* Input dialogs */
QInputDialog {{
    background-color: {COLORS['bg_secondary']};
}}

QInputDialog QLabel {{
    color: {COLORS['text_primary']};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 6px;
    padding: 6px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['accent_blue']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background-color: transparent;
    border: none;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: transparent;
    border: none;
}}
"""

def get_button_style(color='blue', size='medium'):
    """
    Get styled button CSS

    Args:
        color: 'blue', 'green', 'red', or 'grey'
        size: 'small', 'medium', 'large'
    """
    color_map = {
        'blue': (COLORS['accent_blue'], COLORS['accent_blue_hover']),
        'green': (COLORS['accent_green'], COLORS['accent_green_hover']),
        'red': (COLORS['accent_red'], COLORS['accent_red_hover']),
        'grey': (COLORS['bg_tertiary'], COLORS['bg_hover']),
    }

    size_map = {
        'small': ('6px 12px', '11px'),
        'medium': ('8px 16px', '13px'),
        'large': ('10px 20px', '14px'),
    }

    bg_color, hover_color = color_map.get(color, color_map['blue'])
    padding, font_size = size_map.get(size, size_map['medium'])

    return f"""
        QPushButton {{
            background-color: {bg_color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {bg_color};
            opacity: 0.8;
        }}
    """

def get_card_style():
    """Get styled card CSS with shadow"""
    return f"""
        QWidget {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: 8px;
        }}
        QWidget:hover {{
            border-color: {COLORS['border_secondary']};
        }}
    """

def show_message_box(parent, icon, title, text, buttons=None, default_button=None):
    """
    Show a properly styled message box with proper text wrapping

    Args:
        parent: Parent widget
        icon: QMessageBox.Icon (Information, Warning, Critical, Question)
        title: Window title
        text: Message text
        buttons: QMessageBox.StandardButton flags (optional)
        default_button: Default button (optional)

    Returns:
        QMessageBox.StandardButton: The button that was clicked
    """
    from PyQt6.QtWidgets import QMessageBox
    from PyQt6.QtCore import Qt

    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)

    # Enable word wrap for proper text display
    msg_box.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse |
        Qt.TextInteractionFlag.TextSelectableByKeyboard
    )

    if buttons:
        msg_box.setStandardButtons(buttons)
    if default_button:
        msg_box.setDefaultButton(default_button)

    # Find all QLabel children and enable word wrap
    from PyQt6.QtWidgets import QLabel
    for label in msg_box.findChildren(QLabel):
        label.setWordWrap(True)

    return msg_box.exec()


def _show_styled_dialog(parent, title, message, accent_color, hover_color=None):
    """Single-button dialog with configurable accent colour."""
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    if hover_color is None:
        hover_color = accent_color

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumWidth(450)
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {accent_color};
            border-radius: 12px;
        }}
    """)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(40, 40, 40, 40)
    layout.setSpacing(30)

    message_label = QLabel(message)
    message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    message_label.setWordWrap(True)
    message_font = QFont()
    message_font.setPointSize(12)
    message_label.setFont(message_font)
    message_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent; padding: 20px;")
    layout.addWidget(message_label)

    ok_button = QPushButton("OK")
    ok_button.setMinimumWidth(120)
    ok_button.setMinimumHeight(40)
    ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
    ok_button.setStyleSheet(f"""
        QPushButton {{
            background-color: {accent_color}; color: white; border: none;
            border-radius: 6px; padding: 10px 24px; font-size: 14px; font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {hover_color}; }}
    """)
    ok_button.clicked.connect(dialog.accept)

    button_layout = QVBoxLayout()
    button_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addLayout(button_layout)
    dialog.exec()


def show_info_dialog(parent, title, message):
    _show_styled_dialog(parent, title, message, COLORS['accent_blue'], COLORS['accent_blue_hover'])


def show_error_dialog(parent, title, message):
    _show_styled_dialog(parent, title, message, COLORS['accent_red'], COLORS['accent_red_hover'])


def show_warning_dialog(parent, title, message):
    _show_styled_dialog(parent, title, message, COLORS['accent_orange'], '#8B5900')


def show_confirmation_dialog(parent, title, message, buttons=['Save', 'Discard', 'Cancel']):
    """
    Show a modern, centered confirmation dialog with multiple buttons

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message to display
        buttons: List of button labels (default: ['Save', 'Discard', 'Cancel'])

    Returns:
        str: The label of the button that was clicked
    """
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setModal(True)
    dialog.setMinimumWidth(550)

    # Apply dark theme styling
    dialog.setStyleSheet(f"""
        QDialog {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border_primary']};
            border-radius: 12px;
        }}
    """)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(40, 40, 40, 40)
    layout.setSpacing(30)

    # Message label
    message_label = QLabel(message)
    message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    message_label.setWordWrap(True)
    message_font = QFont()
    message_font.setPointSize(12)
    message_label.setFont(message_font)
    message_label.setStyleSheet(f"""
        QLabel {{
            color: {COLORS['text_primary']};
            background-color: transparent;
            padding: 20px;
        }}
    """)
    layout.addWidget(message_label)

    # Buttons layout
    buttons_layout = QHBoxLayout()
    buttons_layout.setSpacing(12)

    dialog.result_value = None

    def create_button_handler(label):
        def handler():
            dialog.result_value = label
            dialog.accept()
        return handler

    # Button styling based on type
    for button_label in buttons:
        btn = QPushButton(button_label)
        btn.setMinimumWidth(120)
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Style based on button type
        if button_label == 'Save':
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_green']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_green_hover']};
                }}
            """)
        elif button_label == 'Discard':
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_red']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_red_hover']};
                }}
            """)
        elif button_label == 'Cancel' or button_label == 'No':
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_tertiary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border_primary']};
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_hover']};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['accent_blue']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_blue_hover']};
                }}
            """)

        btn.clicked.connect(create_button_handler(button_label))
        buttons_layout.addWidget(btn)

    layout.addLayout(buttons_layout)

    dialog.exec()
    return dialog.result_value


def show_yes_no_dialog(parent, title, message):
    """
    Show a modern, centered Yes/No confirmation dialog

    Args:
        parent: Parent widget
        title: Dialog title
        message: Message to display

    Returns:
        bool: True if Yes was clicked, False if No or dialog was closed
    """
    result = show_confirmation_dialog(parent, title, message, buttons=['Yes', 'No'])
    return result == 'Yes'
