from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QStackedLayout, QSizePolicy, QHeaderView
)
from PyQt5.QtGui import QPixmap, QColor, QPalette
from PyQt5.QtCore import pyqtSignal, Qt
import os
from ResourcePath import resource_path


class SnakeGameView(QWidget):
    """
    SnakeGameView: Main view for the Snake mini-game.

    Manages a stacked layout containing:
        - SnakeIndexView: main menu with start button and leaderboard access.
        - SnakeLeaderboardView: displays top players and scores.

    Signals:
        back_to_hub (): Emitted when user wants to return to the main hub.
        start_game (): Emitted when the user starts the game.
        leaderboard_btn_clicked (): Emitted when the leaderboard button is clicked.
        about_to_close (): Emitted when the window is about to close.
    """
    
    back_to_hub: pyqtSignal = pyqtSignal()
    start_game: pyqtSignal = pyqtSignal()
    leaderboard_btn_clicked: pyqtSignal = pyqtSignal()
    about_to_close: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle('xGoalPro - Snake')
        self.setMinimumSize(640, 800)

        # Stacked layout for Index and Leaderboard views
        self.stacked_layout: QStackedLayout = QStackedLayout()

        self.index_view: SnakeIndexView = SnakeIndexView()
        self.leaderboard_view: SnakeLeaderboardView = SnakeLeaderboardView()

        self.stacked_layout.addWidget(self.index_view)
        self.stacked_layout.addWidget(self.leaderboard_view)
        self.setLayout(self.stacked_layout)

        # Connect signals
        self.index_view.start_game.connect(lambda: self.start_game.emit())
        self.index_view.back_to_home.connect(lambda: self.back_to_hub.emit())
        self.index_view.leaderboard_btn_clicked.connect(lambda: self.leaderboard_btn_clicked.emit())
        self.leaderboard_view.return_btn_clicked.connect(self.show_index)

    def show_index(self) -> None:
        self.stacked_layout.setCurrentWidget(self.index_view)

    def show_leaderboard(self) -> None:
        self.stacked_layout.setCurrentWidget(self.leaderboard_view)

    def refresh_leaderboard(self, leaderboard_data) -> None:
        self.leaderboard_view.update_leaderboard(leaderboard_data)

    def closeEvent(self, event):
        self.about_to_close.emit()
        event.accept()


class SnakeIndexView(QWidget):
    """
    SnakeIndexView: Main menu for the Snake game.

    Contains title, subtitle, image/logo, and buttons for starting the game and accessing leaderboard.
    Provides methods to enable/disable buttons during gameplay.

    Signals:
        back_to_home (): Back button signal.
        start_game (): Start game button signal.
        leaderboard_btn_clicked (): Leaderboard button signal.
    """

    back_to_home: pyqtSignal = pyqtSignal()
    start_game: pyqtSignal = pyqtSignal()
    leaderboard_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("SnakeIndexPage")

        # Dark background
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # === Main vertical layout ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 60)
        main_layout.setSpacing(40)

        # --- Top bar with back button ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(0)

        back_btn = QPushButton("Back to Hub")
        back_btn.setObjectName("homeButton")
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(lambda: self.back_to_home.emit())
        top_bar.addWidget(back_btn, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # --- Center content ---
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(25)

        # Title
        title = QLabel("🐍 Snake Game")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(title)

        subtitle = QLabel("The buttons will be inactive (disabled) after startup\n"
        "and will only be reactivated once the game is closed.")
        subtitle.setObjectName("subTitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(subtitle)

        # Image
        img_label = QLabel()
        pixmap = QPixmap(resource_path("./Assets/snake_logo.jpg"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(img_label)

        # Buttons
        start_btn = QPushButton("▶ Start Game")
        start_btn.setObjectName("loginButton")
        start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        start_btn.clicked.connect(lambda: self.start_game.emit())
        center_layout.addWidget(start_btn, alignment=Qt.AlignCenter)

        leaderboard_btn = QPushButton("🏆 Leaderboard")
        leaderboard_btn.setObjectName("loginButton")
        leaderboard_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        leaderboard_btn.clicked.connect(lambda: self.leaderboard_btn_clicked.emit())
        center_layout.addWidget(leaderboard_btn, alignment=Qt.AlignCenter)

        main_layout.addLayout(center_layout)
        self.__load_stylesheet()
        self.setAttribute(Qt.WA_StyledBackground, True)

    def disable_buttons(self) -> None:
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(False)

    def enable_buttons(self) -> None:
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(True)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/snake_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())


class SnakeLeaderboardView(QWidget):
    """
    SnakeLeaderboardView: Leaderboard for Snake game.

    Displays a table of top players and their scores.
    Includes a back button to return to the main game view.

    Signals:
        return_btn_clicked (): Emitted when the "Back to Game" button is pressed.
    """

    return_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("SnakeLeaderboardPage")

        # Dark background
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(80, 50, 80, 50)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title = QLabel("🏆 Snake Leaderboard")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Top Snake Players")
        subtitle.setObjectName("subTitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Table
        self.table = QTableWidget()
        self.table.setObjectName("leaderboardTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rank", "Username", "High Score"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        row_height = 40
        header_height = 45
        self.table.setFixedHeight(header_height + row_height * 10 + 12)
        layout.addWidget(self.table)

        # Back button
        back_button = QPushButton("Back to Game")
        back_button.setObjectName("loginButton")
        back_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        back_button.clicked.connect(lambda: self.return_btn_clicked.emit())
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        self.__load_stylesheet()
        self.setAttribute(Qt.WA_StyledBackground, True)

    def update_leaderboard(self, leaderboard_data) -> None:
        """Leaderboard data is [(rank, username, score), ...]"""
        self.table.setRowCount(len(leaderboard_data))
        for row_idx, (rank, username, score) in enumerate(leaderboard_data):
            for col_idx, text in enumerate([rank, username, score]):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        total_height = 45 + min(len(leaderboard_data), 10) * 40 + 12
        self.table.setFixedHeight(total_height)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/snake_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
