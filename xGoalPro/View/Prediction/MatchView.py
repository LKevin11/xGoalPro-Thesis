from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QGridLayout, QTabWidget, QCheckBox, QFrame, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class MatchH2HCard(QWidget):
    """
    Widget representing a Head-to-Head (H2H) match summary.

    Displays the home and away team names, score, date, and competition.
    """
    def __init__(self, home_team_name, away_team_name, home_score, away_score, date, comp_name):
        super().__init__()
        self.setObjectName("leagueCard")

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        info_row = QHBoxLayout()
        info_row.setAlignment(Qt.AlignCenter)
        comp_label = QLabel(comp_name)
        comp_label.setAlignment(Qt.AlignCenter)
        date_label = QLabel(date)
        date_label.setAlignment(Qt.AlignCenter)

        info_row.addWidget(comp_label)
        info_row.addWidget(date_label)
        layout.addLayout(info_row)

        teams_row = QHBoxLayout()
        teams_row.setAlignment(Qt.AlignCenter)
        home_label = QLabel(home_team_name)
        score_label = QLabel(f"{home_score} : {away_score}")
        away_label = QLabel(away_team_name)
        teams_row.addWidget(home_label)
        teams_row.addWidget(score_label)
        teams_row.addWidget(away_label)
        layout.addLayout(teams_row)

        self.setLayout(layout)
        self.setAttribute(Qt.WA_StyledBackground, True)


class MatchCard(QWidget):
    """
    Widget representing a match available for prediction.

    Shows home and away team names and logos, match date and competition,
    and a "Predict" button that emits the prediction signal.

    Signals:
        predict_match(int, int, int): Emitted when the "Predict" button is clicked.
            Arguments are home_team_id, away_team_id, match_id.
    """
    predict_match: pyqtSignal = pyqtSignal(int, int, int)

    def __init__(self, home_team_name, home_team_image, away_team_name,
                 away_team_image, code, date, comp_name, home_id, away_id):
        super().__init__()
        self.setObjectName("leagueCard")

        self.home_team_name = home_team_name
        self.away_team_name = away_team_name
        self.home_team_image = home_team_image
        self.away_team_image = away_team_image
        self.code = code
        self.date = date
        self.comp_name = comp_name
        self.home_id = home_id
        self.away_id = away_id

        master = QVBoxLayout()
        master.setAlignment(Qt.AlignCenter)
        master.setSpacing(10)

        info = QLabel(f"{self.comp_name} • {self.date}")
        info.setAlignment(Qt.AlignCenter)
        master.addWidget(info)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        home_col = QVBoxLayout()
        away_col = QVBoxLayout()

        home_img = QLabel()
        pix = QPixmap()
        pix.loadFromData(self.home_team_image)
        home_img.setPixmap(pix.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        home_img.setAlignment(Qt.AlignCenter)
        home_label = QLabel(self.home_team_name)
        home_label.setAlignment(Qt.AlignCenter)
        home_col.addWidget(QLabel("HOME"), alignment=Qt.AlignCenter)
        home_col.addWidget(home_img)
        home_col.addWidget(home_label)

        away_img = QLabel()
        pix = QPixmap()
        pix.loadFromData(self.away_team_image)
        away_img.setPixmap(pix.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        away_img.setAlignment(Qt.AlignCenter)
        away_label = QLabel(self.away_team_name)
        away_label.setAlignment(Qt.AlignCenter)
        away_col.addWidget(QLabel("AWAY"), alignment=Qt.AlignCenter)
        away_col.addWidget(away_img)
        away_col.addWidget(away_label)

        vs_label = QLabel("VS")
        vs_label.setAlignment(Qt.AlignCenter)

        row.addLayout(home_col)
        row.addWidget(vs_label)
        row.addLayout(away_col)
        master.addLayout(row)

        btn = QPushButton("Predict")
        btn.setObjectName("leagueCardButton")
        btn.clicked.connect(lambda: self.predict_match.emit(self.home_id, self.away_id, self.code))
        master.addWidget(btn)

        self.setLayout(master)
        self.setAttribute(Qt.WA_StyledBackground, True)


class MatchView(QWidget):
    """
    Main widget for match predictions and H2H history.

    Provides two tabs:
        1. Predictions: Select a match, choose ML models, and view prediction results.
        2. Head-to-Head (H2H): Shows previous matches between the two teams.

    Signals:
        back_to_match_hub: Navigate back to match hub.
        back_to_home: Navigate back to home screen.
        back_to_league_hub: Navigate back to league hub.
        back_to_team_hub: Navigate back to team hub.
        predict_match(int, int, int, list): Emit selected match and chosen ML models.
        no_model_selected: Emitted when prediction attempted without selecting any ML models.
    """
    back_to_match_hub = pyqtSignal()
    back_to_home = pyqtSignal()
    back_to_league_hub = pyqtSignal()
    back_to_team_hub = pyqtSignal()
    predict_match = pyqtSignal(int, int, int, list)
    no_model_selected = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("xGoalPro - Match Prediction")

        self.matches = []
        self.h2h_matches = []
        self.model_checkboxes = {}

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("matchTabWidget")

        self.prediction_tab = QWidget()
        self.h2h_tab = QWidget()

        self.h2h_scroll = QScrollArea()
        self.h2h_scroll.setWidgetResizable(True)

        self.__init_ui()

    def refresh_view(self, match_data, h2h_data, ml_models) -> None:
        self._clear_layout(self.prediction_grid)
        self._clear_layout(self.checkbox_container)
        self._clear_layout(self.result_container)

        # --- Model selection label ---
        label = QLabel("Choose models for prediction (voting system – averages model outputs)\nHover over a checkbox for more information.")
        label.setObjectName("checkboxLabel")
        label.setAlignment(Qt.AlignCenter)
        self.checkbox_container.addWidget(label)

        # --- Add checkboxes ---
        for key, (paths, description) in ml_models.items():
            cb = QCheckBox(key)
            cb.setObjectName("modelCheckbox")
            cb.setChecked(False)
            cb.setToolTip(description)
            self.model_checkboxes[key] = cb
            self.checkbox_container.addWidget(cb)

        # --- Match cards ---
        cols = 3
        for i, m in enumerate(match_data):
            date = m['date'].split("T")[0]
            card = MatchCard(
                m['home_name'], m['home_emblem'],
                m['away_name'], m['away_emblem'],
                m['id'], date, m['competition'],
                m['home_id'], m['away_id']
            )
            card.predict_match.connect(
                lambda home_id, away_id, match_id: self.__on_predict(home_id, away_id, match_id)
            )
            self.prediction_grid.addWidget(card, i // cols, i % cols)

        # --- H2H tab ---
        self._clear_layout(self.h2h_v_layout)
        for h2h in h2h_data:
            card = MatchH2HCard(
                h2h['homeTeam'], h2h['awayTeam'],
                h2h['homeScore'], h2h['awayScore'],
                h2h['date'].split("T")[0], h2h['competition']
            )
            self.h2h_v_layout.addWidget(card)

    def refresh_result(self, data: dict) -> None:
        """Display prediction results inside the styled result container."""
        self._clear_layout(self.result_container)

        # --- Title ---
        title = QLabel("Prediction Result")
        title.setObjectName("resultTitle")
        title.setAlignment(Qt.AlignCenter)
        self.result_container.addWidget(title)

        # --- Separator line ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("resultLine")
        self.result_container.addWidget(line)

        # --- Results ---
        for key, value in data.items():

            if(key.startswith("P_")):
                value_str = f"{value * 100:.2f}"
                label = QLabel(f"<span class='res-key'>{key.replace('_', ' ').title()} (%):</span> "
                               f"<span class='res-val'>{value_str}</span>")
            else:
                value_str = f"{value:.2f}"
                label = QLabel(f"<span class='res-key'>{key.replace('_', ' ').title()}:</span> "
                               f"<span class='res-val'>{value_str}</span>")
            label.setObjectName("resultItem")
            label.setTextFormat(Qt.RichText)
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            self.result_container.addWidget(label)

    def clear_predictions_data(self) -> None:
        self._clear_layout(self.result_container)
        for cb in self.model_checkboxes.values():
            cb.setChecked(False)
        self.back_to_match_hub.emit()

    def __init_ui(self):
        main_layout = QVBoxLayout()
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.clicked.connect(self.back_to_home.emit)

        self.league_hub_btn = QPushButton("Select League")
        self.league_hub_btn.setObjectName("homeButton")
        self.league_hub_btn.clicked.connect(self.back_to_league_hub.emit)

        self.team_hub_btn = QPushButton("Select Team")
        self.team_hub_btn.setObjectName("homeButton")
        self.team_hub_btn.clicked.connect(self.back_to_team_hub.emit)

        self.match_hub_btn = QPushButton("Select Match")
        self.match_hub_btn.setObjectName("homeButton")
        self.match_hub_btn.clicked.connect(self.clear_predictions_data)

        left_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        top_bar.addWidget(self.home_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.league_hub_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.team_hub_btn, alignment=Qt.AlignLeft)
        top_bar.addWidget(self.match_hub_btn, alignment=Qt.AlignLeft)
        top_bar.addItem(left_spacer)
        top_bar.addItem(right_spacer)

        self.title = QLabel("xGoalPro Prediction Center")
        self.title.setObjectName("leagueHubTitle")
        self.title.setAlignment(Qt.AlignCenter)

        # --- Prediction Tab ---
        pred_layout = QVBoxLayout()
        self.checkbox_container = QHBoxLayout()
        self.prediction_grid = QGridLayout()
        self.prediction_grid.setSpacing(15)
        self.result_container = QVBoxLayout()

        pred_layout.addLayout(self.checkbox_container)
        pred_layout.addLayout(self.prediction_grid)
        pred_layout.addLayout(self.result_container)
        self.prediction_tab.setLayout(pred_layout)

        # --- H2H Tab ---
        h2h_container = QWidget()
        self.h2h_v_layout = QVBoxLayout(h2h_container)
        self.h2h_scroll.setWidget(h2h_container)
        h2h_layout = QVBoxLayout()
        h2h_layout.addWidget(self.h2h_scroll)
        self.h2h_tab.setLayout(h2h_layout)

        # --- Tabs ---
        self.tab_widget.addTab(self.prediction_tab, "Predictions")
        self.tab_widget.addTab(self.h2h_tab, "Head 2 Head")

        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.title)
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Apply style
        qss_path = resource_path("./qss/prediction_match_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def __on_predict(self, home_id, away_id, match_id):
        code = [1 if cb.isChecked() else 0 for cb in self.model_checkboxes.values()]
        if sum(code):
            self.predict_match.emit(home_id, away_id, match_id, code)
        else:
            self.no_model_selected.emit()
