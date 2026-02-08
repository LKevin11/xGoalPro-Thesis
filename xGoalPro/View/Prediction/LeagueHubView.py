from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QScrollArea, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class LeagueCard(QWidget):
    """
    LeagueCard: Widget representing a single football league.

    Displays:
        - League emblem/image.
        - League name.
        - Button to view league details.

    Signals:
        view_league(str): Emitted when the user clicks the "View" button, passing the league code.
    """


    view_league: pyqtSignal(str) = pyqtSignal(str)

    def __init__(self, name, image, code):
        super().__init__()
        self.setObjectName("leagueCard")

        self.name: str = name
        self.image: bytes = image
        self.code: str = code

        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setAlignment(Qt.AlignCenter)
        self.master_layout.setSpacing(10)

        # === League image ===
        self.img: QLabel = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(self.image)
        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img.setPixmap(scaled_pixmap)
        self.img.setAlignment(Qt.AlignCenter)

        # === League name ===
        self.name_label: QLabel = QLabel(f"{self.name}")
        self.name_label.setAlignment(Qt.AlignCenter)

        # === View button ===
        self.btn: QPushButton = QPushButton(f"View {self.name}")
        self.btn.setObjectName("leagueCardButton")
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn.clicked.connect(lambda: self.view_league.emit(self.code))

        # === Assemble layout ===
        self.master_layout.addWidget(self.img)
        self.master_layout.addWidget(self.name_label)
        self.master_layout.addWidget(self.btn)
        self.setLayout(self.master_layout)
        self.setAttribute(Qt.WA_StyledBackground, True)


class LeagueHubView(QWidget):
    """
    LeagueHubView: Main hub for football prediction leagues.

    Contains:
        - Home/back button.
        - Title label.
        - Scrollable grid of LeagueCard widgets.

    Signals:
        back_to_home(): Emitted when the home button is pressed.
        show_league(str): Emitted when a specific league is selected.

    Methods:
        refresh_view(leagues_data): Clears and repopulates the grid with updated league data.
        leagues_data is a list of dicts, each with keys: 'name', 'emblem' (bytes), 'code'.
    """


    back_to_home: pyqtSignal = pyqtSignal()
    show_league: pyqtSignal(str) = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setObjectName("LeagueHubPage")
        self.setWindowTitle("xGoalPro - Prediction LeagueHub")

        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setSpacing(15)

        # === Home/Back button ===
        self.home_btn: QPushButton = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.home_btn.clicked.connect(lambda: self.back_to_home.emit())

        # === Title ===
        self.title: QLabel = QLabel("xGoalPro Prediction LeagueHub\nSelect League")
        self.title.setObjectName("leagueHubTitle")
        self.title.setAlignment(Qt.AlignCenter)

        # === Scroll Area ===
        self.scroll: QScrollArea = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.grid: QGridLayout = QGridLayout(container)
        self.grid.setSpacing(15)
        container.setLayout(self.grid)
        self.scroll.setWidget(container)

        # === Assemble ===
        self.master_layout.addWidget(self.home_btn, alignment=Qt.AlignLeft)
        self.master_layout.addWidget(self.title)
        self.master_layout.addWidget(self.scroll)
        self.setLayout(self.master_layout)

        # === Apply shared QSS theme ===
        qss_path = resource_path("./qss/prediction_league_hub.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def refresh_view(self, leagues_data) -> None:
        """Refresh the grid with the latest leagues data."""
        # Clear old widgets
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Create and add new league cards
        columns = 3
        for i, league in enumerate(leagues_data):
            card = LeagueCard(league['name'], league['emblem'], league['code'])
            card.view_league.connect(lambda code: self.show_league.emit(code))
            self.grid.addWidget(card, i // columns, i % columns)
