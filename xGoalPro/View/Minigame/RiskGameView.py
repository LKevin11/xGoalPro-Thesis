from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedLayout,
    QHBoxLayout, QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPalette
import os
from ResourcePath import resource_path


class RiskGameView(QWidget):
    """
    The main view for Football Risk mini-game.

    Manages a stacked layout containing the game index and leaderboard views.
    Provides signals for returning to hub and interacting with game actions.

    Signals:
        return_to_hub (): Emitted when the user wants to return to the main hub.
        advance_btn_clicked (): Emitted when the "Advance" button is pressed.
        hold_btn_clicked (): Emitted when the "Hold" button is pressed.
        new_btn_clicked (): Emitted when starting a new attack.
        reset_btn_clicked (): Emitted when resetting the game progress.
        leaderboard_btn_clicked (): Emitted when the leaderboard button is pressed.
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    advance_btn_clicked: pyqtSignal = pyqtSignal()
    hold_btn_clicked: pyqtSignal = pyqtSignal()
    new_btn_clicked: pyqtSignal = pyqtSignal()
    reset_btn_clicked: pyqtSignal = pyqtSignal()
    leaderboard_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("RiskPage")
        self.setWindowTitle("Football Risk — Advance or Hold")
        self.setMinimumSize(1000, 700)

        # === Dark background ===
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Stacked layout for Index and Leaderboard
        self.stacked_layout: QStackedLayout = QStackedLayout()
        self.index_view: RiskIndexView = RiskIndexView()
        self.leaderboard_view: RiskLeaderboardView = RiskLeaderboardView()

        self.stacked_layout.addWidget(self.index_view)
        self.stacked_layout.addWidget(self.leaderboard_view)
        self.setLayout(self.stacked_layout)

        # Connect signals
        self.index_view.return_to_hub.connect(lambda: self.return_to_hub.emit())
        self.index_view.advance_btn_clicked.connect(lambda: self.advance_btn_clicked.emit())
        self.index_view.hold_btn_clicked.connect(lambda: self.hold_btn_clicked.emit())
        self.index_view.new_btn_clicked.connect(lambda: self.new_btn_clicked.emit())
        self.index_view.reset_btn_clicked.connect(lambda: self.reset_btn_clicked.emit())
        self.index_view.leaderboard_btn.clicked.connect(lambda: self.leaderboard_btn_clicked.emit())

        self.leaderboard_view.return_btn_clicked.connect(self.show_index)

        # Load stylesheet
        self.__load_stylesheet()

    def show_index(self) -> None:
        self.stacked_layout.setCurrentWidget(self.index_view)

    def show_leaderboard(self) -> None:
        self.stacked_layout.setCurrentWidget(self.leaderboard_view)

    def append_log(self, text) -> None:
        self.index_view.append_log(text)

    def update_scores(self, bank, current, position, high) -> None:
        self.index_view.update_scores(bank, current, position, high)

    def refresh_leaderboard(self, leaderboard_data) -> None:
        self.leaderboard_view.update_leaderboard(leaderboard_data)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/risk_game_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())


class RiskIndexView(QWidget):
    """
    The index view for Football Risk.

    Contains title, scoreboard, pitch progress bar, action buttons, log area, and status label.
    Emits signals for button actions.

    Signals:
        return_to_hub (): Back button signal.
        advance_btn_clicked (): Advance/Risk button.
        hold_btn_clicked (): Hold/Bank button.
        new_btn_clicked (): New Attack button.
        reset_btn_clicked (): Reset Progress button.
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    advance_btn_clicked: pyqtSignal = pyqtSignal()
    hold_btn_clicked: pyqtSignal = pyqtSignal()
    new_btn_clicked: pyqtSignal = pyqtSignal()
    reset_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(25)

        # --- Top Bar (Back Button) ---
        top_bar = QHBoxLayout()
        self.return_btn: QPushButton = QPushButton("Back to Hub")
        self.return_btn.setObjectName("homeButton")
        self.return_btn.clicked.connect(lambda: self.return_to_hub.emit())
        top_bar.addWidget(self.return_btn, alignment=Qt.AlignLeft)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # --- Title ---
        title = QLabel("Football Risk — Advance or Hold")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --- Scoreboard ---
        self.lbl_bank = QLabel("Bank: 0")
        self.lbl_current = QLabel("Current Attack: 0")
        self.lbl_position = QLabel("Pitch Position: 0")
        self.lbl_high = QLabel("High Score: 0")

        for lbl in (self.lbl_bank, self.lbl_current, self.lbl_position, self.lbl_high):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setObjectName("scoreLabel")
            layout.addWidget(lbl)

        # --- Progress Bar ---
        self.pitch_pb = QProgressBar()
        self.pitch_pb.setRange(0, 100)
        self.pitch_pb.setValue(0)
        layout.addWidget(self.pitch_pb)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_advance = QPushButton("Advance (Risk)")
        self.btn_hold = QPushButton("Hold (Bank)")
        self.btn_new = QPushButton("New Attack")
        self.btn_reset = QPushButton("Reset Progress")
        self.leaderboard_btn = QPushButton("Leaderboard")

        self.btn_advance.clicked.connect(lambda: self.advance_btn_clicked.emit())
        self.btn_hold.clicked.connect(lambda: self.hold_btn_clicked.emit())
        self.btn_new.clicked.connect(lambda: self.new_btn_clicked.emit())
        self.btn_reset.clicked.connect(lambda: self.reset_btn_clicked.emit())

        for btn in (
            self.btn_advance, self.btn_hold,
            self.btn_new, self.btn_reset, self.leaderboard_btn
        ):
            btn.setObjectName("actionButton")
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        # --- Log Area ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("logBox")
        layout.addWidget(self.log)

        # --- Status ---
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setObjectName("statusLabel")
        layout.addWidget(self.status)

        self.setLayout(layout)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def append_log(self, text) -> None:
        self.log.append(text)

    def update_scores(self, bank, current, position, high) -> None:
        self.lbl_bank.setText(f"Bank: {bank}")
        self.lbl_current.setText(f"Current Attack: {current}")
        self.lbl_position.setText(f"Pitch Position: {position}")
        self.lbl_high.setText(f"High Score: {high}")
        self.pitch_pb.setValue(min(max(position, 0), 100))


class RiskLeaderboardView(QWidget):
    """
    Leaderboard view for Football Risk.

    Displays a table of top players and their high scores.
    Contains a return button to go back to the main game view.

    Signals:
        return_btn_clicked (): Emitted when the "Back to Game" button is pressed.
    """

    return_btn_clicked: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("LeaderboardPage")

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0d1b2a"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(80, 60, 80, 60)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignCenter)

        # --- Title ---
        self.title = QLabel("🏆 Leaderboard")
        self.title.setObjectName("leaderboardTitle")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setObjectName("leaderboardTable")
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Rank", "Username", "High Score"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
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

        # --- Return button ---
        self.return_button = QPushButton("Back to Game")
        self.return_button.setObjectName("leaderboardHomeButton")
        self.return_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.return_button.clicked.connect(lambda: self.return_btn_clicked.emit())
        layout.addWidget(self.return_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setAttribute(Qt.WA_StyledBackground, True)

    def update_leaderboard(self, leaderboard_data) -> None:
        """Leaderboard data is [(rank, username, score), ...]"""
        self.table.setRowCount(len(leaderboard_data))
        for row_idx, (rank, username, score) in enumerate(leaderboard_data):
            for col, value in enumerate((rank, username, score)):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col, item)

        total_height = 45 + min(len(leaderboard_data), 10) * 40 + 12
        self.table.setFixedHeight(total_height)
