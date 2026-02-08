import ast
import os
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
)
from ResourcePath import resource_path

import pandas as pd


from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QTabWidget, QPushButton
)

class LeagueTableWidget(QWidget):
    """
    Widget displaying a league standings table.
    Emblem shown next to team name.
    """
    team_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Instruction label
        self.info_label = QLabel(
            "💡 Tip: Click on a team name to view detailed team statistics.\n"
            "Hover over a column header for more information."
        )
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Team", "M", "W", "D", "L", "GF", "GA", "PTS"]
        )

        header_tooltips = [
            "Team name with emblem",
            "Matches played",
            "Wins",
            "Draws",
            "Losses",
            "Goals scored",
            "Goals against",
            "Points"
        ]

        header = self.table.horizontalHeader()
        for i, tip in enumerate(header_tooltips):
            header.model().setHeaderData(i, Qt.Horizontal, tip, Qt.ToolTipRole)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self.__on_cell_clicked)
        layout.addWidget(self.table)

        self._team_data = []

    def update_table(self, teams) -> None:
        """
        Update table with league standings.
        teams: list of dicts with keys:
            'id', 'name', 'emblem' (bytes), 'playedGames', 'won', 'draw',
            'lost', 'goalsFor', 'goalsAgainst', 'points'
        """
        self.table.setRowCount(len(teams))
        self._team_data = teams

        for row_idx, team in enumerate(teams):
            # Team name + emblem
            pixmap = QPixmap()
            pixmap.loadFromData(team["emblem"])
            icon = QIcon(pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            item = QTableWidgetItem(team["name"])
            item.setIcon(icon)
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            item.setToolTip(team["name"])
            self.table.setItem(row_idx, 0, item)
            self.table.setRowHeight(row_idx, 32)

            # Stats columns
            stats = [
                team["playedGames"], team["won"], team["draw"], team["lost"],
                team["goalsFor"], team["goalsAgainst"], team["points"]
            ]
            for col_idx, value in enumerate(stats, start=1):
                stat_item = QTableWidgetItem(str(value))
                stat_item.setTextAlignment(Qt.AlignCenter)

                # Highlight PTS column (last column)
                if col_idx == 7:
                    stat_item.setForeground(QColor("#15181E"))
                    stat_item.setBackground(QColor("#00b87b"))

                stat_item.setToolTip(str(value))
                self.table.setItem(row_idx, col_idx, stat_item)

    def __on_cell_clicked(self, row, column):
        team_id = self._team_data[row]["id"]
        self.team_clicked.emit(team_id)
        self.table.clearSelection()


class TopScorersWidget(QWidget):
    """
    Widget showing top scorers.
    Team emblem displayed next to team name.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Instruction
        self.info_label = QLabel("💡 Tip: Hover over a column header for more information.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Player", "Games", "Goals", "Assists", "Team"])

        header_tooltips = [
            "Player name",
            "Games played",
            "Goals scored",
            "Assists made",
            "Team name with emblem"
        ]
        header = self.table.horizontalHeader()
        for i, tip in enumerate(header_tooltips):
            header.model().setHeaderData(i, Qt.Horizontal, tip, Qt.ToolTipRole)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def update_table(self, players) -> None:
        """
        Update table with top 20 players.
        players: list of dicts with keys:
            'player_name', 'playedMatches', 'goals', 'assists', 'name' (team), 'emblem' (bytes)
        """
        players = players[:20]
        self.table.setRowCount(len(players))

        for row_idx, player in enumerate(players):
            # Player name
            item = QTableWidgetItem(player["player_name"])
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(player["player_name"])
            self.table.setItem(row_idx, 0, item)

            # Games, Goals, Assists
            for col, key in enumerate(["playedMatches", "goals", "assists"], start=1):
                val_item = QTableWidgetItem(str(player[key]))
                val_item.setTextAlignment(Qt.AlignCenter)
                val_item.setToolTip(str(player[key]))
                self.table.setItem(row_idx, col, val_item)

            # Team name + emblem
            team_item = QTableWidgetItem(player["name"])
            team_item.setTextAlignment(Qt.AlignCenter)
            team_item.setToolTip(player["name"])
            self.table.setItem(row_idx, 4, team_item)
            self.table.setRowHeight(row_idx, 32)


class ResultsWidget(QWidget):
    """
    Widget showing recent or completed match results.
    Emblems displayed next to team names.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Home", "Score", "Away", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def update_table(self, results) -> None:
        """
        results: list of dicts with keys:
            'home_name', 'home_emblem', 'score', 'away_name', 'away_emblem', 'date'
        """
        self.table.setRowCount(len(results))

        for row_idx, match in enumerate(results):
            # Home team + emblem
            home_item = QTableWidgetItem(match["home_name"])
            home_item.setTextAlignment(Qt.AlignCenter)
            home_item.setToolTip(match["home_name"])
            self.table.setItem(row_idx, 0, home_item)

            # Score
            score_item = QTableWidgetItem(match["score"])
            score_item.setTextAlignment(Qt.AlignCenter)
            score_item.setToolTip(match["score"])
            self.table.setItem(row_idx, 1, score_item)

            # Away team + emblem
            away_item = QTableWidgetItem(match["away_name"])
            away_item.setTextAlignment(Qt.AlignCenter)
            away_item.setToolTip(match["away_name"])
            self.table.setItem(row_idx, 2, away_item)

            # Date
            date_item = QTableWidgetItem(match["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setToolTip(match["date"])
            self.table.setItem(row_idx, 3, date_item)

            self.table.setRowHeight(row_idx, 32)


class StatisticsLeagueView(QWidget):
    """
    Main view for displaying league-level statistics.

    Composed of three tab widgets:
        - LeagueTableWidget (league standings)
        - TopScorersWidget (player stats)
        - ResultsWidget (recent match results)

    Signals:
        back_to_home: Emitted when Home button is clicked.
        back_to_index: Emitted when Back to Hub button is clicked.
        back_to_league_hub: Emitted when Select League button is clicked.
        team_clicked (str): Emitted when a team is clicked in the league table.

    Methods:
        refresh_view(data): Update all tabs with new data.
            Args:
                data (list): [table_df, players_df, results_df], each a pandas DataFrame.

    Layout:
        - Top bar with Home, Back, and Select League buttons + page title
        - Tabs: League Table, Top Scorers, Results
    """
    back_to_home = pyqtSignal()
    back_to_index = pyqtSignal()
    back_to_league_hub = pyqtSignal()
    team_clicked = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("StatisticsLeagueView")
        self.__init_ui()
        self.__load_stylesheet()

    def refresh_view(self, data):
        """
        Expects a list: [table_df, players_df, results_df]
        """
        teams, players, results = data

        self.league_table_tab.update_table(teams)
        self.top_scorers_tab.update_table(players)
        self.results_tab.update_table(results)

    def __init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        self.setWindowTitle("xGoalPro - League statistics")
        self.setMinimumSize(800, 600)

        # Header with Back button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        self.home_button: QPushButton = QPushButton("🏠 Home")
        self.home_button.setObjectName("homeButton")
        self.home_button.setFixedWidth(160)
        self.home_button.clicked.connect(self.back_to_home.emit)

        self.index_btn: QPushButton = QPushButton("Back to Hub")
        self.index_btn.setObjectName("homeButton")
        self.index_btn.setFixedWidth(160)
        self.index_btn.clicked.connect(self.back_to_index.emit)

        self.league_hub_btn: QPushButton = QPushButton("Select League")
        self.league_hub_btn.setObjectName("homeButton")
        self.league_hub_btn.setFixedWidth(160)
        self.league_hub_btn.clicked.connect(self.back_to_league_hub.emit)

        title_label = QLabel("League Statistics")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignCenter)

        top_bar.addWidget(self.home_button)
        top_bar.addWidget(self.index_btn)
        top_bar.addWidget(self.league_hub_btn)
        top_bar.addStretch()
        top_bar.addWidget(title_label)
        top_bar.addStretch()

        # Tabs
        self.tabs: QTabWidget = QTabWidget()
        self.tabs.setObjectName("statsTabs")

        self.league_table_tab: LeagueTableWidget = LeagueTableWidget()
        self.top_scorers_tab: TopScorersWidget = TopScorersWidget()
        self.results_tab: ResultsWidget = ResultsWidget()

        self.league_table_tab.team_clicked.connect(self.team_clicked.emit)

        self.tabs.addTab(self.league_table_tab, "League Table")
        self.tabs.addTab(self.top_scorers_tab, "Top Scorers")
        self.tabs.addTab(self.results_tab, "Results")

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.tabs)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/statistics_league_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
