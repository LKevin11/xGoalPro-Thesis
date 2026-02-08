from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import os
from ResourcePath import resource_path


class StatisticsIndexView(QWidget):
    """
    Main dashboard view for accessing statistics in xGoalPro.

    Provides navigation to:
        - Team and Player Statistics
        - Prediction Statistics

    Signals:
        back_to_home: Emitted when the "Home" button is clicked.
        team_stats_btn_clicked: Emitted when the "Team and Player Statistics" button is clicked.
        prediction_statistics_btn_clicked: Emitted when the "Prediction Statistics" button is clicked.
    """
    back_to_home = pyqtSignal()
    team_stats_btn_clicked = pyqtSignal()
    prediction_statistics_btn_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("StatisticsIndexPage")
        self.setWindowTitle("xGoalPro - Statistics")

        self.__init_ui()
        self.__load_stylesheet()

    def __init_ui(self):
        # === Root layout ===
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(80, 50, 80, 50)
        root_layout.setSpacing(20)

        # === Top bar ===
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignLeft)

        home_btn = QPushButton("🏠 Home")
        home_btn.setObjectName("homeButton")
        home_btn.clicked.connect(lambda: self.back_to_home.emit())
        top_bar.addWidget(home_btn)

        root_layout.addLayout(top_bar)

        # === Headline ===
        headline = QLabel("Statistics Dashboard")
        headline.setObjectName("titleLabel")
        headline.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(headline)

        # === Subtitle ===
        sub_headline = QLabel("Analyze team and prediction performance in one place")
        sub_headline.setObjectName("subTitleLabel")
        sub_headline.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(sub_headline)

        # === App Logo ===
        logo_label = QLabel()
        logo_path = resource_path("./Assets/team-stats.jpg")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(360, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("xGoalPro")
            logo_label.setStyleSheet("font-size: 40px; color: #00b87b; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignCenter)
        root_layout.addWidget(logo_label)

        # === Buttons Layout ===
        btn_layout = QVBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(25)

        # --- Team Stats ---
        team_btn = QPushButton("Team and Player Statistics")
        team_btn.setObjectName("statButton")
        team_btn.clicked.connect(lambda: self.team_stats_btn_clicked.emit())
        btn_layout.addWidget(team_btn, alignment=Qt.AlignCenter)

        # --- Prediction Stats ---
        pred_btn = QPushButton("Prediction Statistics")
        pred_btn.setObjectName("statButton")
        pred_btn.clicked.connect(lambda: self.prediction_statistics_btn_clicked.emit())
        btn_layout.addWidget(pred_btn, alignment=Qt.AlignCenter)

        root_layout.addLayout(btn_layout)

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/statistics_index.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
