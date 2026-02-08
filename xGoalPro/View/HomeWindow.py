from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QDesktopWidget
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QSize
import os
from ResourcePath import resource_path


class HomeWindow(QWidget):
    """
    Main home screen for xGoalPro application.

    Provides navigation to the main services of the app:
        - Prediction
        - Statistics
        - Mini Game
        - Training

    Signals:
        switch_to_prediction: Emitted when the Prediction button is clicked.
        switch_to_statistics: Emitted when the Statistics button is clicked.
        switch_to_minigame: Emitted when the Mini Game button is clicked.
        switch_to_training: Emitted when the Training button is clicked.

    Layout:
        - Logo at top center
        - Welcome message
        - Instruction message
        - Four large navigation buttons arranged horizontally, each with icon and label

    Styling:
        - Uses external QSS file located at "./qss/home_window.qss"
    """
    switch_to_prediction = pyqtSignal()
    switch_to_statistics = pyqtSignal()
    switch_to_minigame = pyqtSignal()
    switch_to_training = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("xGoalPro")
        self.setObjectName("HomeWindow")

        # === Main layout ===
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(80, 60, 80, 60)
        main_layout.setSpacing(40)

        # === Logo ===
        logo_label = QLabel()
        logo_path = resource_path("./Assets/logo.png")
        pixmap = QPixmap(logo_path)
        pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)

        # === Welcome Label ===
        welcome_label = QLabel("Welcome to xGoalPro")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setObjectName("welcomeLabel")

        # === Instruction Label ===
        info_label = QLabel("Choose a service to get started ⚽")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setObjectName("infoLabel")

        # === Buttons layout ===
        button_layout = QHBoxLayout()
        button_layout.setSpacing(50)
        button_layout.setAlignment(Qt.AlignCenter)

        # Button setup helper
        def create_button(text, icon_path):
            btn = QPushButton(text)
            btn.setIcon(QIcon(resource_path(icon_path)))
            btn.setIconSize(QSize(70, 70))
            btn.setMinimumSize(220, 160)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName("menuButton")
            return btn

        # === Buttons ===
        assets_dir = "./Assets"
        self.prediction_menu_btn = create_button("Prediction", os.path.join(assets_dir, "pred-icon.png"))
        self.statistics_menu_btn = create_button("Statistics", os.path.join(assets_dir, "statistics-icon.png"))
        self.minigame_menu_btn = create_button("Mini Game", os.path.join(assets_dir, "minigame-icon.png"))
        self.training_menu_btn = create_button("Training", os.path.join(assets_dir, "training-icon.png"))

        button_layout.addWidget(self.prediction_menu_btn)
        button_layout.addWidget(self.statistics_menu_btn)
        button_layout.addWidget(self.minigame_menu_btn)
        button_layout.addWidget(self.training_menu_btn)

        # === Add everything to layout ===
        main_layout.addWidget(logo_label)
        main_layout.addSpacing(10)
        main_layout.addWidget(welcome_label)
        main_layout.addWidget(info_label)
        main_layout.addSpacing(20)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.__init_connections()

        # Load stylesheet
        qss_path = resource_path("./qss/home_window.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def __init_connections(self):
        self.prediction_menu_btn.clicked.connect(lambda: self.switch_to_prediction.emit())
        self.statistics_menu_btn.clicked.connect(lambda: self.switch_to_statistics.emit())
        self.minigame_menu_btn.clicked.connect(lambda: self.switch_to_minigame.emit())
        self.training_menu_btn.clicked.connect(lambda: self.switch_to_training.emit())
