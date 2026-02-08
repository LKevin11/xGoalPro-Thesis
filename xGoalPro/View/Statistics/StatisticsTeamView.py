import os
import ast
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from ResourcePath import resource_path


class TeamPlayersWidget(QWidget):
    """
    Widget showing individual player statistics for a team.

    Columns include:
        - Player name, Position
        - Games played, Minutes
        - Goals, Expected goals (xG)
        - Assists, Expected assists (xA)
        - Key passes
        - Yellow/Red cards

    Methods:
        update_table(df): Populate the table with a pandas DataFrame of players.
    """

    def __init__(self, team_json=None):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Team info label
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setOpenExternalLinks(True)
        self.info_label.setObjectName("infoLabel")
        self.layout.addWidget(self.info_label)

        # Squad table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Position", "Date of Birth", "Nationality"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)

        # Coach info label
        self.coach_label = QLabel()
        self.coach_label.setAlignment(Qt.AlignCenter)
        self.coach_label.setObjectName("infoLabel")
        self.layout.addWidget(self.coach_label)

        if team_json:
            self.update_table(team_json)

    def update_table(self, team_json: dict):
        """
        Update the widget with new team JSON data.
        """
        # Update team info
        team_name = team_json.get("name", "")
        team_area = team_json.get("area", {}).get("name", "")
        founded = team_json.get("founded", "")
        venue = team_json.get("venue", "")
        website = team_json.get("website", "#")
        self.info_label.setText(
            f"<b>{team_name}</b> ({team_area})<br>"
            f"Founded: {founded}<br>"
            f"Stadium: {venue}<br>"
            f"<a href='{website}' style='color: white;'>{website}</a>"
        )

        # Update squad table
        squad = team_json.get("squad", [])
        self.table.setRowCount(len(squad))
        for row_idx, player in enumerate(squad):
            self.table.setItem(row_idx, 0, QTableWidgetItem(player.get("name", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(player.get("position", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(player.get("dateOfBirth", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(player.get("nationality", "")))

        # Update coach info
        coach = team_json.get("coach")
        if coach:
            self.coach_label.setText(
                f"<b>Coach:</b> {coach.get('name', '')} ({coach.get('nationality', '')})<br>"
                f"Contract: {coach.get('contract', {}).get('start', '')} to {coach.get('contract', {}).get('until', '')}"
            )
        else:
            self.coach_label.setText("")


class TeamResultsWidget(QWidget):
    """
    Widget showing past match results for a team.

    Columns include:
        - Home team
        - Scoreline (H-A)
        - Away team
        - Date of match

    Methods:
        update_table(df): Populate the table with a pandas DataFrame of results.
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


class StatisticsTeamView(QWidget):
    """
    Main view for displaying detailed team statistics.

    Composed of three tabs:
        - TeamPlayersWidget: Player statistics
        - TeamResultsWidget: Team results
        - TeamStatsWidget: Offensive/defensive metrics by category

    Signals:
        back_to_home: Emitted when Home button is clicked.
        back_to_index: Emitted when Back to Hub button is clicked.
        back_to_league_hub: Emitted when Select League button is clicked.
        back_to_league: Emitted when League Stats button is clicked.

    Methods:
        refresh_view(data): Update all tabs with new data.
            Args:
                data (list): [players_df, results_df, stats_dict]

    Layout:
        - Top bar with navigation buttons + page title
        - Tabs: Players, Results, Stats
    """
    back_to_home = pyqtSignal()
    back_to_index = pyqtSignal()
    back_to_league_hub = pyqtSignal()
    back_to_league = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("StatisticsTeamView")
        self.setWindowTitle("xGoalPro - Team and Player Statistics")
        self.__init_ui()
        self.__load_stylesheet()

    def refresh_view(self, data) -> None:
        """Called by controller: [players_df, results_df, stats_dict]"""
        players_df, results_df = data
        self.players_tab.update_table(players_df)
        self.results_tab.update_table(results_df)

    def __init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        self.setMinimumSize(800, 600)

        # --- Header bar ---
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        self.back_button = QPushButton("🏠 Home")
        self.back_button.setObjectName("backButton")
        self.back_button.setFixedWidth(160)
        self.back_button.clicked.connect(self.back_to_home.emit)

        self.index_btn = QPushButton("Back to Hub")
        self.index_btn.setObjectName("backButton")
        self.index_btn.setFixedWidth(160)
        self.index_btn.clicked.connect(self.back_to_index.emit)

        self.league_hub_btn = QPushButton("Select League")
        self.league_hub_btn.setObjectName("backButton")
        self.league_hub_btn.setFixedWidth(160)
        self.league_hub_btn.clicked.connect(self.back_to_league_hub.emit)

        self.league_btn = QPushButton("League Stats")
        self.league_btn.setObjectName("backButton")
        self.league_btn.setFixedWidth(160)
        self.league_btn.clicked.connect(self.back_to_league.emit)

        title_label = QLabel("Team Statistics")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignCenter)

        top_bar.addWidget(self.back_button)
        top_bar.addWidget(self.index_btn)
        top_bar.addWidget(self.league_hub_btn)
        top_bar.addWidget(self.league_btn)
        top_bar.addStretch()
        top_bar.addWidget(title_label)
        top_bar.addStretch()

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.setObjectName("statsTabs")

        self.players_tab = TeamPlayersWidget()
        self.results_tab = TeamResultsWidget()

        self.tabs.addTab(self.players_tab, "Players")
        self.tabs.addTab(self.results_tab, "Results")

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.tabs)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/statistics_team_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
