from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                             QScrollArea, QGridLayout, QSizePolicy, QHBoxLayout, QSpacerItem)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class LeagueCard(QWidget):
    """
    A card widget representing a single league.

    Displays the league's emblem, short name, and a button to view the league.

    Signals:
        view_league (str): Emitted when the "View" button is clicked, passing the league's long name.

    Args:
        name (str): Short name of the league.
        image (bytes): Binary image data for the league emblem.
        code (str): Internal code of the league.
        long_name (str): Full descriptive name of the league.
    """
    view_league: pyqtSignal(str) = pyqtSignal(str)

    def __init__(self, name, image, code, long_name):
        super().__init__()
        self.setObjectName("leagueCard")

        self.name: str = name
        self.image: bytes = image
        self.code: str = code
        self.long_name: str = long_name

        self.master_layout = QVBoxLayout()
        self.master_layout.setAlignment(Qt.AlignCenter)
        self.master_layout.setSpacing(10)

        # League image
        self.img: QLabel = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(self.image)
        scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.img.setPixmap(scaled_pixmap)
        self.img.setAlignment(Qt.AlignCenter)

        # League name
        self.name_label: QLabel = QLabel(f"{self.name}")
        self.name_label.setAlignment(Qt.AlignCenter)

        # View button
        self.btn: QPushButton = QPushButton(f"View {self.name}")
        self.btn.setObjectName("leagueCardButton")
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn.clicked.connect(lambda: self.view_league.emit(self.long_name))

        # Add widgets
        self.master_layout.addWidget(self.img)
        self.master_layout.addWidget(self.name_label)
        self.master_layout.addWidget(self.btn)
        self.setLayout(self.master_layout)
        self.setAttribute(Qt.WA_StyledBackground, True)


class StatisticsLeagueHubView(QWidget):
    """
    Hub view for selecting a league in the Statistics module.

    Provides a scrollable grid of leagues and top navigation buttons.

    Signals:
        back_to_home: Emitted when the "Home" button is clicked.
        back_to_index: Emitted when the "Back to Hub" button is clicked.
        show_league (str): Emitted when a league card's view button is clicked, passing the league's long name.

    Public Methods:
        refresh_view(leagues_data): Refreshes the league grid with new data.

    Layout:
        - Top bar: Home button, Back to Hub button, spacing.
        - Title: Centered label showing the current hub name.
        - Scrollable grid: Displays LeagueCard widgets in a 3-column grid.

    Args:
        None (constructor initializes the view and loads styles from QSS).
    """
    back_to_home: pyqtSignal = pyqtSignal()
    back_to_index: pyqtSignal = pyqtSignal()
    show_league: pyqtSignal(str) = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("xGoalPro - League selection")

        self.setObjectName("LeagueHubPage")
        self.master_layout = QVBoxLayout()
        self.master_layout.setSpacing(15)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # === Back/Home button ===
        self.home_btn: QPushButton = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.home_btn.clicked.connect(lambda: self.back_to_home.emit())

        self.index_btn: QPushButton = QPushButton("Back to Hub")
        self.index_btn.setObjectName("homeButton")
        self.index_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.index_btn.clicked.connect(lambda: self.back_to_index.emit())

        left_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        top_bar.addWidget(self.home_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.index_btn, alignment=Qt.AlignLeft)
        top_bar.addItem(left_spacer)
        top_bar.addItem(right_spacer)

        # === Title ===
        self.title: QLabel = QLabel("xGoalPro LeagueHub\nSelect League")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setObjectName("leagueHubTitle")

        # === Scroll area ===
        self.scroll: QScrollArea = QScrollArea()
        self.scroll.setWidgetResizable(True)

        container = QWidget()
        self.grid: QGridLayout = QGridLayout(container)
        self.grid.setSpacing(15)
        container.setLayout(self.grid)
        self.scroll.setWidget(container)

        # Add widgets to layout
        self.master_layout.addLayout(top_bar)
        self.master_layout.addWidget(self.title)
        self.master_layout.addWidget(self.scroll)
        self.setLayout(self.master_layout)

        # Load QSS
        qss_path = resource_path("./qss/stat_league_hub.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def refresh_view(self, leagues_data) -> None:
        # Clear previous widgets
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Populate grid with new leagues
        columns = 3
        for i, league in enumerate(leagues_data):
            card = LeagueCard(league['name'], league['emblem'], league['code'], league['long_name'])
            card.view_league.connect(lambda code: self.show_league.emit(code))
            self.grid.addWidget(card, i // columns, i % columns)
