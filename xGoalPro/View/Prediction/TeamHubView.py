from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class TeamCard(QWidget):
    """
    Widget representing a single team card in the TeamHub.

    Displays the team emblem, name, and a "View" button to emit
    a signal with the team's unique ID.
    
    Signals:
        view_team(int): Emitted when the "View" button is clicked, carrying
                        the team's ID.
    """

    view_team: pyqtSignal(int) = pyqtSignal(int)

    def __init__(self, name, image, code):
        super().__init__()
        self.setObjectName("leagueCard")  # reuse same style block

        self.name: str = name
        self.image: bytes = image
        self.code: int = code

        # === Layout ===
        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setAlignment(Qt.AlignCenter)
        self.master_layout.setSpacing(10)

        # === Team image ===
        self.img: QLabel = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(self.image)
        scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img.setPixmap(scaled_pixmap)
        self.img.setAlignment(Qt.AlignCenter)

        # === Team name ===
        self.name_label: QLabel = QLabel(f"{self.name}")
        self.name_label.setAlignment(Qt.AlignCenter)

        # === View button ===
        self.btn = QPushButton(f"View {self.name}")
        self.btn.setObjectName("leagueCardButton")
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn.clicked.connect(lambda: self.view_team.emit(self.code))

        # === Assemble ===
        self.master_layout.addWidget(self.img)
        self.master_layout.addWidget(self.name_label)
        self.master_layout.addWidget(self.btn)
        self.setLayout(self.master_layout)
        self.setAttribute(Qt.WA_StyledBackground, True)


class TeamHubView(QWidget):
    """
    Main hub for browsing teams within a league.

    Provides a scrollable grid of TeamCards and top navigation buttons
    to return to the league hub or home.

    Signals:
        back_to_league_hub: Navigate back to the League Hub view.
        back_to_home: Navigate back to the main/home screen.
        show_team(int): Emit the ID of the selected team to view its details.
    """

    back_to_league_hub: pyqtSignal = pyqtSignal()
    back_to_home: pyqtSignal = pyqtSignal()
    show_team: pyqtSignal(int) = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.setObjectName("LeagueHubPage")
        self.setWindowTitle("xGoalPro - TeamHub")

        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setSpacing(15)

        # === Top Bar (Back Button + Title) ===
        self.top_bar = QHBoxLayout()
        self.top_bar.setSpacing(10)
        self.home_btn: QPushButton = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.home_btn.clicked.connect(lambda: self.back_to_home.emit())

        self.league_hub_btn: QPushButton = QPushButton("Select League")
        self.league_hub_btn.setObjectName("homeButton")
        self.league_hub_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.league_hub_btn.clicked.connect(lambda: self.back_to_league_hub.emit())

        self.title: QLabel = QLabel("xScore TeamHub\nSelect Team")
        self.title.setObjectName("leagueHubTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.top_bar.addWidget(self.home_btn, alignment=Qt.AlignLeft)
        self.top_bar.addWidget(self.league_hub_btn, alignment=Qt.AlignLeft)
        self.top_bar.addWidget(self.title, stretch=1, alignment=Qt.AlignCenter)
        self.top_bar.addStretch()

        # === Scroll area for team grid ===
        self.scroll: QScrollArea = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid: QGridLayout = QGridLayout(container)
        self.grid.setSpacing(15)
        container.setLayout(self.grid)
        self.scroll.setWidget(container)

        # === Assemble main layout ===
        self.master_layout.addLayout(self.top_bar)
        self.master_layout.addWidget(self.scroll)
        self.setLayout(self.master_layout)

        # === Apply shared QSS styling ===
        qss_path = resource_path("./qss/team_hub_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def refresh_view(self, team_data) -> None:
        """Refresh grid with updated team data."""
        self.title.setText(f"{team_data[1]}\nSelect Team")

        # Clear old widgets
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Add new team cards
        columns = 5
        for i, team in enumerate(team_data[0]):
            card = TeamCard(team['name'], team['emblem'], team['id'])
            card.view_team.connect(lambda code: self.show_team.emit(code))
            self.grid.addWidget(card, i // columns, i % columns)
