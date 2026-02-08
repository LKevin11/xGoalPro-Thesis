from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
import os
from ResourcePath import resource_path


class LoadingWidget(QWidget):
    """
    A custom QWidget that displays a loading animation with an accompanying text label.

    This widget is designed to provide a visual indicator of ongoing processing
    using an animated GIF. It centers both the animation and the text label
    within a vertical layout. A QSS stylesheet can be applied for custom styling
    if found at the predefined path.

    Attributes:
        movie (QMovie): The animated GIF used for the loading animation.
        gif_label (QLabel): The label widget displaying the GIF animation.
        text_label (QLabel): The label widget displaying the loading message.
    """
    def __init__(self, gif_path: str, label_text: str = "Loading..."):
        super().__init__()
        self.setWindowTitle("xGoalPro")
        self.setObjectName("LoadingWidget")

        # === Loading GIF ===
        self.movie = QMovie(resource_path(gif_path))
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMovie(self.movie)

        # === Text Label ===
        self.text_label = QLabel(label_text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setObjectName("loadingText")

        # === Layout ===
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        layout.addWidget(self.gif_label)
        layout.addWidget(self.text_label)
        self.setLayout(layout)

        # Start the animation
        self.movie.start()

        # === Load QSS stylesheet ===
        qss_path = resource_path("./qss/loading_widget.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def set_label(self, text: str):
        """Update the text displayed below the loading animation."""
        self.text_label.setText(text)
