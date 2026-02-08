from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class GameCard(QWidget):
    """
    A QWidget representing an individual game card.

    Displays the game's image, name, description, and a button to start the game.
    Clicking the card or the button emits a signal with the game's index.

    Signals:
        view_game (int): Emitted when the card or its button is clicked, passing
            the index of the game.

    Attributes:
        idx (int): Index of the game.
        name (str): Name of the game.
        des (str): Description of the game.
        image (str): Path to the game's image.
    """

    view_game: pyqtSignal(int) = pyqtSignal(int)

    def __init__(self, idx, name, des, image):
        super().__init__()

        self.idx: int = idx
        self.name: str = name
        self.des: str = des
        self.image: str = image

        self.setObjectName("GameCard")

        # === Layout ===
        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setSpacing(15)
        self.master_layout.setContentsMargins(20, 20, 20, 20)
        self.master_layout.setAlignment(Qt.AlignCenter)

        # === Image ===
        self.img: QLabel = QLabel()
        pixmap = QPixmap(resource_path(self.image))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img.setPixmap(scaled_pixmap)
        else:
            self.img.setText("No Image")
        self.img.setAlignment(Qt.AlignCenter)

        # === Texts ===
        self.name_label: QLabel = QLabel(f"{self.name}")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)

        self.des_label: QLabel = QLabel(f"{self.des}")
        self.des_label.setAlignment(Qt.AlignCenter)
        self.des_label.setWordWrap(True)
        self.des_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # === Button ===
        self.btn = QPushButton("Start Game")
        self.btn.setObjectName("viewGameButton")
        self.btn.clicked.connect(lambda: self.view_game.emit(self.idx))

        # === Add widgets ===
        self.master_layout.addWidget(self.img)
        self.master_layout.addWidget(self.name_label)
        self.master_layout.addWidget(self.des_label, 1)
        self.master_layout.addWidget(self.btn, alignment=Qt.AlignBottom)

        self.setLayout(self.master_layout)
        self.setFixedWidth(260)
        self.setMinimumHeight(360)

        self.__load_stylesheet()
        self.setAttribute(Qt.WA_StyledBackground, True)

    def mousePressEvent(self, event):
        """Emit signal when card is clicked"""
        if event.button() == Qt.LeftButton:
            self.view_game.emit(self.idx)
        super().mousePressEvent(event)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/game_card.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
