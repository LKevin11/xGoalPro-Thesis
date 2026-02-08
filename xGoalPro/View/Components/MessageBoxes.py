from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import os
from ResourcePath import resource_path


class CustomMessageBox(QDialog):
    """
    A custom modal message box for displaying messages with a title, content area, and buttons.

    This widget provides a flexible dialog layout featuring a title label, a read-only
    text area for displaying content, and customizable buttons. It supports applying
    an external QSS stylesheet for consistent visual styling.

    Attributes:
        title_label (QLabel): Displays the message box title.
        content_text (QTextEdit): Read-only text area showing the main message content.
        ok_button (QPushButton): Default confirmation button to close the dialog.
        header_layout (QHBoxLayout): Layout containing the title label.
        button_layout (QHBoxLayout): Layout managing action buttons.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("xGoalPro")

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("CustomMessageBox")
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
        self.setModal(True)

        # Widgets
        self.title_label = QLabel()
        self.title_label.setObjectName("titleLabel")

        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setObjectName("contentText")

        self.ok_button = QPushButton("OK")
        self.ok_button.setObjectName("okButton")
        self.ok_button.clicked.connect(self.close)

        # Layouts
        self.header_layout = QHBoxLayout()
        self.header_layout.addWidget(self.title_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignCenter)
        self.button_layout.addWidget(self.ok_button)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(15)

        main_layout.addLayout(self.header_layout)
        main_layout.addWidget(self.content_text)
        main_layout.addLayout(self.button_layout)

        self.setLayout(main_layout)
        self.setMinimumWidth(420)

        # Load stylesheet
        qss_path = resource_path("./qss/message_box.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_content(self, content: str) -> None:
        self.content_text.setPlainText(content)

    def add_button(self, btn_label: str, fn) -> None:
        new_btn = QPushButton(btn_label)
        new_btn.setObjectName("extraButton")
        new_btn.clicked.connect(fn)
        self.button_layout.addWidget(new_btn)


class ErrorMessageBox(CustomMessageBox):
    """
    A specialized message box for displaying error messages.

    This subclass of CustomMessageBox automatically formats a list of
    error messages into a bullet-point list and sets a warning title
    and icon to indicate an error state.
    """
    def __init__(self, errors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error")
        self.set_title("⚠️ The following errors occurred:")
        self.set_content("\n".join(f"• {error}" for error in errors))
        self.setWindowIcon(QIcon(resource_path("./Assets/icon.ico")))
        self.ok_button.setText("Close")


class InfoMessageBox(CustomMessageBox):
    """
    A specialized message box for displaying informational messages.

    This subclass of CustomMessageBox formats a list of information items
    into a bullet-point list and sets an informational title and icon.
    """
    def __init__(self, information, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.set_title("Information:")
        self.set_content("\n".join(f"• {info}" for info in information))
        self.setWindowIcon(QIcon(resource_path("./Assets/icon.ico")))
        self.ok_button.setText("OK")
