from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QGridLayout, QTabWidget, QCalendarWidget, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt, QDate
from PyQt5.QtGui import QPixmap, QPainter
import os
from ResourcePath import resource_path


class MatchCard(QWidget):
    """
    A widget representing a single football match card.

    Displays the home and away team names and logos, match date, and a
    button to view the match. Emits a signal with match data when the
    button is clicked.

    Signals:
        view_match(dict): Emitted when the "View Match" button is clicked.
    """
    view_match: pyqtSignal = pyqtSignal(dict)

    def __init__(self, home_team_name, home_team_image, away_team_name,
                 away_team_image, code, date, comp_name, home_id, away_id):
        super().__init__()
        self.setObjectName("leagueCard")

        self.home_team_name: str = home_team_name
        self.home_team_image: bytes = home_team_image
        self.away_team_name: str = away_team_name
        self.away_team_image: bytes = away_team_image
        self.code: int = code
        self.date: str = date
        self.comp_name: str = comp_name
        self.home_id: int = home_id
        self.away_id: int = away_id

        # === Layouts ===
        self.master_layout: QVBoxLayout = QVBoxLayout()
        self.master_layout.setAlignment(Qt.AlignCenter)
        self.master_layout.setSpacing(10)

        self.teams_row: QHBoxLayout = QHBoxLayout()
        self.teams_row.setAlignment(Qt.AlignCenter)
        self.home_team_col: QVBoxLayout = QVBoxLayout()
        self.away_team_col: QVBoxLayout = QVBoxLayout()

        # === Date ===
        self.date_label: QLabel = QLabel(self.date)
        self.date_label.setAlignment(Qt.AlignCenter)

        # === Home team ===
        self.home_img: QLabel = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(self.home_team_image)
        scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.home_img.setPixmap(scaled_pixmap)
        self.home_img.setAlignment(Qt.AlignCenter)
        self.home_label: QLabel = QLabel(self.home_team_name)
        self.home_label.setAlignment(Qt.AlignCenter)

        self.home_team_col.addWidget(self.home_img)
        self.home_team_col.addWidget(self.home_label)
        self.teams_row.addLayout(self.home_team_col)

        # === VS Label ===
        self.vs_label: QLabel = QLabel("VS")
        self.vs_label.setAlignment(Qt.AlignCenter)
        self.teams_row.addWidget(self.vs_label)

        # === Away team ===
        self.away_img: QLabel = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(self.away_team_image)
        scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.away_img.setPixmap(scaled_pixmap)
        self.away_img.setAlignment(Qt.AlignCenter)
        self.away_label: QLabel = QLabel(self.away_team_name)
        self.away_label.setAlignment(Qt.AlignCenter)

        self.away_team_col.addWidget(self.away_img)
        self.away_team_col.addWidget(self.away_label)
        self.teams_row.addLayout(self.away_team_col)

        # === View button ===
        self.btn: QPushButton = QPushButton("View Match")
        self.btn.setObjectName("leagueCardButton")

        data = {
            "id": self.code,
            "home_name": self.home_team_name,
            "home_emblem": self.home_team_image,
            "away_name": self.away_team_name,
            "away_emblem": self.away_team_image,
            "date": self.date,
            "competition": self.comp_name,
            "home_id": self.home_id,
            "away_id": self.away_id
        }
        self.btn.clicked.connect(lambda: self.view_match.emit(data))

        # === Assemble layout ===
        self.master_layout.addWidget(self.date_label)
        self.master_layout.addLayout(self.teams_row)
        self.master_layout.addWidget(self.btn)
        self.setLayout(self.master_layout)
        self.setAttribute(Qt.WA_StyledBackground, True)


class MatchCalendar(QCalendarWidget):
    """
    Custom QCalendarWidget to display football matches with team logos.

    Each date cell can display small icons representing matches scheduled
    on that date.

    Methods:
        set_matches(matches): Populate the calendar with match data.
        paintCell(painter, rect, date): Override to draw match icons.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.match_images: dict = {}
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setGridVisible(True)

    def set_matches(self, matches) -> None:
        """Store matches with icons for rendering."""
        self.match_images.clear()
        for match in matches:
            qdate = QDate.fromString(match['date'].split("T")[0], "yyyy-MM-dd")

            # Home emblem
            pix_home = QPixmap()
            pix_home.loadFromData(match['home_emblem'])
            pix_home = pix_home.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Away emblem
            pix_away = QPixmap()
            pix_away.loadFromData(match['away_emblem'])
            pix_away = pix_away.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            self.match_images.setdefault(qdate, []).extend([pix_home, pix_away])

        self.updateCells()

    def paintCell(self, painter, rect, date) -> None:
        """Custom draw calendar cells with match images."""
        super().paintCell(painter, rect, date)
        if date in self.match_images:
            icons = self.match_images[date]
            x = rect.x() + 5
            y = rect.y() + rect.height() - 30
            for pix in icons:
                painter.drawPixmap(x, y, pix)
                x += 28


class MatchHubView(QWidget):
    """
    Main hub for selecting football matches.

    Provides two views:
        1. List/Grid view of MatchCard widgets.
        2. Calendar view showing matches on their scheduled dates.

    Signals:
        back_to_home: Emitted when navigating back to the home page.
        back_to_league_hub: Emitted when navigating to league hub.
        back_to_team_hub: Emitted when navigating to team hub.
        show_match(dict): Emitted when a match is selected.
    """
    back_to_team_hub: pyqtSignal = pyqtSignal()
    back_to_home: pyqtSignal = pyqtSignal()
    back_to_league_hub: pyqtSignal = pyqtSignal()
    show_match: pyqtSignal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.matches: list = []

        self.setWindowTitle("xGoalPro - Match Selection")

        # Tabs
        self.tab_widget: QTabWidget = QTabWidget()
        self.tab_widget.setObjectName("matchTabWidget")

        self.list_tab: QWidget = QWidget()
        self.calendar_tab: QWidget = QWidget()

        # List tab widgets
        self.scroll: QScrollArea = QScrollArea()
        self.scroll.setWidgetResizable(True)

        # Calendar tab
        self.calendar: MatchCalendar = MatchCalendar()

        self.__init_ui()

    def refresh_view(self, match_data) -> None:
        """Populate both list and calendar views."""
        self.matches = match_data
        if not match_data:
            self.title.setText("No match found")
            return

        self.title.setText("Select Match")

        # === List View ===
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(15)
        columns = 5
        for i, match in enumerate(match_data):
            date = match['date']
            formatted_date = date.split("T")[0]
            card = MatchCard(
                match['home_name'], match['home_emblem'],
                match['away_name'], match['away_emblem'],
                match['id'], formatted_date, match['competition'],
                match['home_id'], match['away_id']
            )
            card.view_match.connect(lambda data: self.show_match.emit(data))
            grid.addWidget(card, i // columns, i % columns)
        self.scroll.setWidget(container)

        # === Calendar View ===
        self.calendar.set_matches(match_data)

    def __init_ui(self) -> None:
        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Header
        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.clicked.connect(lambda: self.back_to_home.emit())

        self.league_hub_btn = QPushButton("Select League")
        self.league_hub_btn.setObjectName("homeButton")
        self.league_hub_btn.clicked.connect(lambda: self.back_to_league_hub.emit())

        self.team_hub_btn = QPushButton("Select Team")
        self.team_hub_btn.setObjectName("homeButton")
        self.team_hub_btn.clicked.connect(lambda: self.back_to_team_hub.emit())

        left_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        top_bar.addWidget(self.home_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.league_hub_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.team_hub_btn, alignment=Qt.AlignLeft)
        top_bar.addItem(left_spacer)
        top_bar.addItem(right_spacer)

        self.title = QLabel("xScore MatchHub")
        self.title.setObjectName("leagueHubTitle")
        self.title.setAlignment(Qt.AlignCenter)

        # === List View ===
        list_layout = QVBoxLayout()
        list_layout.addWidget(self.scroll)
        self.list_tab.setLayout(list_layout)

        # === Calendar View ===
        cal_layout = QVBoxLayout()
        cal_layout.addWidget(self.calendar)
        self.calendar_tab.setLayout(cal_layout)

        # === Tabs ===
        self.tab_widget.addTab(self.list_tab, "List View")
        self.tab_widget.addTab(self.calendar_tab, "Calendar View")

        # === Final Layout ===
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.title)
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Connect calendar date click
        self.calendar.clicked.connect(self.__on_date_selected)

        # Load global style
        qss_path = resource_path("./qss/prediction_match_hub.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def __on_date_selected(self, qdate) -> None:
        """Show matches for the selected date"""
        date_str = qdate.toString("yyyy-MM-dd")
        day_matches = [m for m in self.matches if m['date'].startswith(date_str)]
        if not day_matches:
            return
        match = day_matches[0]
        data = {
            "id": match["id"],
            "home_name": match["home_name"],
            "home_emblem": match['home_emblem'],
            "away_name": match['away_name'],
            "away_emblem": match['away_emblem'],
            "date": date_str,
            "competition": match['competition'],
            "home_id": match['home_id'],
            "away_id": match['away_id']
        }
        self.show_match.emit(data)
