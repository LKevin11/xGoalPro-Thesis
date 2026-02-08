import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedLayout,
    QTableWidget, QTableWidgetItem, QDesktopWidget, QSizePolicy, QHeaderView
)
from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPalette
from Assets.utils import lane_to_x, WINDOW_H, WINDOW_W, PLAYER_Y
from ResourcePath import resource_path


class DribbleKingView(QWidget):
    """
    The main container widget for the Dribble King mini-game.

    This class manages switching between the main game interface and the
    leaderboard view using a QStackedLayout. It coordinates signals from
    the child views to control navigation, gameplay, and leaderboard updates.

    Signals:
        return_to_hub (): Emitted when the player chooses to exit to the hub.
        move_left (): Emitted when the player presses the move-left key.
        move_right (): Emitted when the player presses the move-right key.
        restart_clicked (): Emitted when the player requests to restart.
        leaderboard_btn_clicked (): Emitted when the leaderboard is opened.
        start_game (): Emitted when the game is started.
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    move_left: pyqtSignal = pyqtSignal()
    move_right: pyqtSignal = pyqtSignal()
    restart_clicked: pyqtSignal = pyqtSignal()
    leaderboard_btn_clicked: pyqtSignal = pyqtSignal()
    start_game: pyqtSignal = pyqtSignal()

    def __init__(self, model):
        super().__init__()

        self.setFixedSize(480, 800)

        self.setWindowTitle('xGoalPro - DribbleKing')
        self.model = model

        # Stacked layout for Index and Leaderboard views
        self.stacked_layout: QStackedLayout = QStackedLayout()

        self.index_view: DribbleKingIndexView = DribbleKingIndexView(model)
        self.leaderboard_view: DribbleKingLeaderboardView = DribbleKingLeaderboardView()

        self.stacked_layout.addWidget(self.index_view)
        self.stacked_layout.addWidget(self.leaderboard_view)

        self.setLayout(self.stacked_layout)

        # Connect signals
        self.index_view.return_to_hub.connect(lambda: self.return_to_hub.emit())
        self.index_view.move_left.connect(lambda: self.move_left.emit())
        self.index_view.move_right.connect(lambda: self.move_right.emit())
        self.index_view.restart_clicked.connect(lambda: self.restart_clicked.emit())
        self.index_view.leaderboard_btn_clicked.connect(lambda: self.show_leaderboard())
        self.index_view.start_game.connect(lambda: self.start_game.emit())

        self.leaderboard_view.return_btn_clicked.connect(lambda: self.show_index())

        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

    def showEvent(self, event):
        """Center window when shown."""
        super().showEvent(event)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def show_index(self) -> None:
        self.model.reset()
        self.model.timer.start(16)
        self.stacked_layout.setCurrentWidget(self.index_view)

    def show_leaderboard(self) -> None:
        self.model.timer.stop()
        self.leaderboard_btn_clicked.emit()
        self.stacked_layout.setCurrentWidget(self.leaderboard_view)

    def refresh_leaderboard(self, leaderboard_data) -> None:
        self.leaderboard_view.update_leaderboard(leaderboard_data)


class DribbleKingIndexView(QWidget):
    """
    The main gameplay view for the Dribble King mini-game.

    This widget renders the game environment, player, and obstacles.
    It handles user input for movement and game control, drawing the
    background, game objects, and overlays for score, start instructions,
    and game over messages.

    Signals:
        return_to_hub (): Emitted when the "BACK" button is clicked.
        move_left (): Emitted when the player moves left.
        move_right (): Emitted when the player moves right.
        restart_clicked (): Emitted when the restart key (R) is pressed.
        leaderboard_btn_clicked (): Emitted when the "Leaderboard" button is clicked.
        start_game (): Emitted when the player starts the game (S key).
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    move_left: pyqtSignal = pyqtSignal()
    move_right: pyqtSignal = pyqtSignal()
    restart_clicked: pyqtSignal = pyqtSignal()
    leaderboard_btn_clicked: pyqtSignal = pyqtSignal()
    start_game: pyqtSignal = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setFixedSize(WINDOW_W, WINDOW_H)

        self.game_started: bool = False

        self.bg_img: QPixmap = QPixmap(resource_path("./Assets/background.png"))
        self.ball_img: QPixmap = QPixmap(resource_path("./Assets/ball.png"))
        self.cone_img: QPixmap = QPixmap(resource_path("./Assets/cone.png"))

        # Quit button
        self.home_btn: QPushButton = QPushButton("BACK", self)
        self.home_btn.move(WINDOW_W - 100, 20)
        self.home_btn.clicked.connect(lambda: self.return_to_hub.emit())
        self.home_btn.setStyleSheet("background-color: #415a77; color: white;")

        # Leaderboard button
        self.leaderboard_btn: QPushButton = QPushButton("Leaderboard", self)
        self.leaderboard_btn.move(WINDOW_W - 200, 20)
        self.leaderboard_btn.clicked.connect(lambda: self.leaderboard_btn_clicked.emit())
        self.leaderboard_btn.setStyleSheet("background-color: #415a77; color: white;")

        self.__load_stylesheet()

    def keyPressEvent(self, event):
        if not self.game_started:
            if event.key() == Qt.Key_S:
                self.game_started = True
                self.start_game.emit()
            return

        if event.key() in (Qt.Key_Left, Qt.Key_A):
            self.move_left.emit()
        elif event.key() in (Qt.Key_Right, Qt.Key_D):
            self.move_right.emit()
        elif event.key() == Qt.Key_R:
            if self.model.game_over:
                self.restart_clicked.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        p.drawPixmap(self.rect(), self.bg_img, self.bg_img.rect())

        if self.game_started:
            # Draw obstacles
            for obs in self.model.obstacles:
                r = obs.rect()
                p.drawPixmap(r.toRect(), self.cone_img, self.cone_img.rect())

            # Draw ball
            px = lane_to_x(self.model.lane)
            py = PLAYER_Y + self.model.ball_offset - 40
            ball_rect = QRect(int(px - self.model.ball_radius),
                              int(py - self.model.ball_radius),
                              int(2 * self.model.ball_radius),
                              int(2 * self.model.ball_radius))
            p.drawPixmap(ball_rect, self.ball_img, self.ball_img.rect())

            # Score
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Arial", 18, QFont.Bold))
            p.drawText(16, 34, f"Score: {self.model.score}")

            if self.model.game_over:
                p.setPen(QColor(240, 60, 60))
                p.setFont(QFont("Arial", 34, QFont.Bold))
                p.drawText(self.rect(), Qt.AlignCenter, "GAME OVER\nPress R to restart")
        else:
            # Draw overlay instructions
            p.setPen(QColor(255, 255, 255))
            p.setFont(QFont("Arial", 16, QFont.Bold))
            overlay_text = (
                "Welcome to Dribble King!\n\n"
                "Goal: Dribble the ball between\n cones as long as possible.\n\n"
                "Controls: A = Move Left,\n D = Move Right\n"
                "Press S to start!"
            )
            p.drawText(self.rect(), Qt.AlignCenter, overlay_text)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/dribble_leaderboard.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())


class DribbleKingLeaderboardView(QWidget):
    """
    The leaderboard view for the Dribble King mini-game.

    Displays the top player scores in a styled table format.
    It supports up to 10 leaderboard entries and provides a button
    for returning to the main game interface.

    Signals:
        return_btn_clicked (): Emitted when the "Back to Game" button is clicked.

    Attributes:
        table (QTableWidget): Table widget displaying rank, username, and score data.
    """

    return_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("LeaderboardPage")

        # Force dark background via palette to override white QWidget default
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # === Root layout ===
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(80, 50, 80, 50)
        root_layout.setSpacing(25)
        root_layout.setAlignment(Qt.AlignCenter)

        # === Title ===
        title = QLabel("🏆 Leaderboard")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(title)

        sub_title = QLabel("Top Dribblers of All Time")
        sub_title.setObjectName("subTitleLabel")
        sub_title.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(sub_title)

        # === Table ===
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

        # Reserve space for up to 10 rows
        row_height = 38
        max_rows = 10
        header_height = 40
        self.table.setFixedHeight(header_height + row_height * max_rows + 8)

        root_layout.addWidget(self.table)

        # === Bottom button ===
        back_button = QPushButton("Back to Game")
        back_button.setObjectName("loginButton")  # reuse login button style
        back_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        back_button.clicked.connect(lambda: self.return_btn_clicked.emit())
        root_layout.addWidget(back_button, alignment=Qt.AlignCenter)

        # === Load QSS ===
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

        # Adjust height for current number of rows (up to 10)
        base_height = 40  # header
        row_height = 38
        total_height = base_height + min(len(leaderboard_data), 10) * row_height + 8
        self.table.setFixedHeight(total_height)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/dribble_leaderboard.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
