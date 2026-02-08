from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from GameProperties import GameProperties
from View.Minigame.GameCard import GameCard
import os
from ResourcePath import resource_path


class MiniGameHubView(QWidget):
    """
    The hub view for accessing all available minigames in xGoalPro.

    Displays a welcome message to the current user and a grid of game cards.
    Provides a home button to return to the main hub and emits signals when
    a game card is selected.

    Signals:
        back_to_home (): Emitted when the user clicks the home button.
        show_game (int): Emitted when the user selects a game, passing the game's index.

    Attributes:
        _current_user (str): The username of the current user.
        _user_id (int): The ID of the current user.
        _games (list[GameProperties]): List of games available in the hub.
    """

    back_to_home: pyqtSignal = pyqtSignal()
    show_game: pyqtSignal(int) = pyqtSignal(int)

    def __init__(self, user, user_id, games):
        super().__init__()
        self.setWindowTitle("xGoalPro - Minigame Hub")

        self.setObjectName("MiniGameHubView")
        self._current_user: str = user
        self._user_id: int = user_id
        self._games: list[GameProperties] = games

        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setSpacing(40)  # bigger gap between rows
        self.master_layout.setContentsMargins(40, 30, 40, 30)

        # === Home button ===
        self.home_btn: QPushButton = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.clicked.connect(lambda: self.back_to_home.emit())

        # === Title ===
        self.title: QLabel = QLabel(f"xGoalPro MinigameHub\nWelcome {self._current_user}")
        self.title.setObjectName("titleLabel")
        self.title.setAlignment(Qt.AlignCenter)

        self.master_layout.addWidget(self.home_btn, alignment=Qt.AlignLeft)
        self.master_layout.addWidget(self.title, alignment=Qt.AlignCenter)

        # === Games section ===
        self.__init_games()
        self.setLayout(self.master_layout)
        self.__load_stylesheet()

    def update_content(self, user, user_id, games) -> None:
        """Update the hub view with new user and game data"""
        self._current_user = user
        self._user_id = user_id
        self._games = games
        self.title.setText(f"xGoalPro MinigameHub\nWelcome {self._current_user}")
        self.__init_games()

    def __init_games(self) -> None:
        # Remove previous rows
        for i in reversed(range(self.master_layout.count())):
            item = self.master_layout.itemAt(i)
            if isinstance(item, QHBoxLayout):
                for j in reversed(range(item.count())):
                    widget = item.itemAt(j).widget()
                    if widget:
                        widget.deleteLater()
                self.master_layout.removeItem(item)

        # Add game cards in rows of 4
        idx = 0
        row_layout = None

        for game in self._games:
            if idx % 4 == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(40)  # bigger horizontal gap between cards
                row_layout.setAlignment(Qt.AlignCenter)
                self.master_layout.addLayout(row_layout)

            game_card = GameCard(idx, game.name, game.description, game.image)
            game_card.view_game.connect(lambda g=idx: self.show_game.emit(g))
            row_layout.addWidget(game_card)
            idx += 1

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/minigame_hub_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
