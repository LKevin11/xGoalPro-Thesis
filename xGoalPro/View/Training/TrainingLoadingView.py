from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtCore import Qt
import os
from ResourcePath import resource_path


class TrainingLoadingView(QWidget):
    """
    GUI for displaying the progress of training Support Vector Regression (SVR) models.

    Layout:
        - Header label indicating training in progress
        - Read-only text area for logging messages from the training process
        - Back button to return to the training configuration page (initially disabled)

    Features:
        - append_log(message: str): Add a message to the log text area
        - clear_log(): Clear all log messages
        - enable_button(): Enable the Back button after training completes
        - disable_button(): Disable the Back button while training is ongoing

    Styling:
        - Uses external QSS file located at "./qss/training_loading_view.qss"
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xGoalPro - Training Progress")
        self.setObjectName("TrainingLoadingView")

        # === Main layout ===
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(100, 80, 100, 80)
        layout.setSpacing(30)

        # === Header Label ===
        self.label = QLabel("Training SVR models... please wait.")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setObjectName("trainingLabel")

        # === Log Text Area ===
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("logBox")

        # === Back Button ===
        self.back_button = QPushButton("⬅ Back to Training")
        self.back_button.setObjectName("secondaryButton")
        self.back_button.setEnabled(False)

        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.log_box)
        layout.addWidget(self.back_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

        # === Load stylesheet ===
        qss_path = resource_path("./qss/training_loading_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    # === Public methods ===
    def append_log(self, message: str) -> None:
        self.log_box.append(message)

    def clear_log(self) -> None:
        self.log_box.clear()

    def enable_button(self) -> None:
        self.back_button.setEnabled(True)

    def disable_button(self) -> None:
        self.back_button.setEnabled(False)
