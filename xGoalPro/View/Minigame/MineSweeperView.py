from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QColor, QPalette
import os
from ResourcePath import resource_path


class MineSweeperView(QWidget):
    """
    The main view for the MineSweeper mini-game.

    Displays the game's title, logo, instructions, and a start button.
    Provides a back button to return to the hub and emits signals for
    starting the game and handling view closure.

    Signals:
        back_to_hub (): Emitted when the user clicks the back button.
        start_game (): Emitted when the user clicks the start button.
        about_to_close (): Emitted when the window is about to close.
    """


    back_to_hub = pyqtSignal()
    start_game = pyqtSignal()
    about_to_close = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("MineSweeperPage")
        self.setWindowTitle("xGoalPro - MineSweeper Game")

        # === Dark background ===
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # === Root layout ===
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(60, 40, 60, 60)
        root_layout.setSpacing(40)

        # === Top bar (back button only) ===
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        back_btn = QPushButton("Back to Hub")
        back_btn.setObjectName("homeButton")
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(lambda: self.back_to_hub.emit())
        top_bar.addWidget(back_btn, alignment=Qt.AlignLeft)
        top_bar.addStretch()

        root_layout.addLayout(top_bar)

        # === Center content ===
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(25)

        # --- Title ---
        title = QLabel("💣 MineSweeper")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        subtitle = QLabel("The buttons will be inactive (disabled) after startup\n"
        "and will only be reactivated once the game is closed.")
        subtitle.setObjectName("subTitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle)

        # --- Image ---
        img_label = QLabel()
        pixmap = QPixmap(resource_path("./Assets/minesweeper_logo.jpg"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(img_label)

        # --- Start Button ---
        start_btn = QPushButton("▶ Start Game")
        start_btn.setObjectName("loginButton")
        start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        start_btn.clicked.connect(lambda: self.start_game.emit())
        content_layout.addWidget(start_btn, alignment=Qt.AlignCenter)

        root_layout.addLayout(content_layout)

        # Load QSS
        self.__load_stylesheet()

    def disable_buttons(self) -> None:
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(False)

    def enable_buttons(self) -> None:
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)

    def closeEvent(self, event):
        self.about_to_close.emit()
        event.accept()

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/minesweeper_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
