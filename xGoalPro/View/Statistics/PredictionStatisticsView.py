import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QScrollArea, QSizePolicy, QPushButton,
    QFrame, QSpacerItem
)
from PyQt5.QtCore import pyqtSignal, Qt
import pandas as pd
import os
from ResourcePath import resource_path


class PredictionStatisticsView(QWidget):
    """
    View for displaying prediction statistics in xGoalPro.

    Provides an interactive dashboard with:
        - Visual charts of expected goals, predicted probabilities, and model averages
        - Table view of all match predictions and actual results
        - Navigation buttons for returning to home or statistics index

    Signals:
        back_to_home: Emitted when the "Home" button is clicked.
        back_to_index: Emitted when the "Back to Hub" button is clicked.

    Public Methods:
        clear_layout(): Clears all existing charts and table content.
        refresh_view(data_list): Populates charts and table using the given prediction data.

    Internally:
        __generate_figures(df): Generates matplotlib figures for charts.
        __create_match_table(df): Builds a QTableWidget from prediction DataFrame.
        __load_stylesheet(): Loads the QSS stylesheet for consistent UI styling.
    """
    back_to_home: pyqtSignal = pyqtSignal()
    back_to_index: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PredictionStatsPage")
        self.setWindowTitle("xGoalPro - Prediction Statistics")

        self.setMinimumSize(800, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(20)

        # === Top bar (centered title) ===
        top_bar = QHBoxLayout()
        top_bar.setSpacing(0)

        self.index_btn = QPushButton("Back to Hub")
        self.index_btn.setObjectName("homeButton")
        self.index_btn.clicked.connect(lambda: self.back_to_index.emit())

        self.home_btn = QPushButton("🏠 Home")
        self.home_btn.setObjectName("homeButton")
        self.home_btn.clicked.connect(lambda: self.back_to_home.emit())

        left_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        right_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        title_label = QLabel("Prediction Statistics Dashboard")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)

        top_bar.setSpacing(10)
        top_bar.addWidget(self.home_btn)
        top_bar.addWidget(self.index_btn)
        top_bar.addItem(left_spacer)
        top_bar.addWidget(title_label, 0, Qt.AlignCenter)
        top_bar.addItem(right_spacer)
        main_layout.addLayout(top_bar)

        # === Tabs ===
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        self.tabs.setMovable(True)
        self.tabs.setUsesScrollButtons(True)
        main_layout.addWidget(self.tabs)

        # --- Charts Tab ---
        self.charts_tab = QWidget()
        charts_tab_layout = QVBoxLayout(self.charts_tab)
        charts_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.charts_tab, "Plots")

        # Scroll area for charts
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setObjectName("scrollArea")

        self.charts_container = QWidget()
        self.charts_container.setObjectName("chartsContainer")
        self.scroll_layout = QHBoxLayout(self.charts_container)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.charts_container)

        charts_tab_layout.addWidget(self.scroll_area)

        # --- Table Tab ---
        self.table_tab = QWidget()
        self.table_layout = QVBoxLayout(self.table_tab)
        self.table_layout.setContentsMargins(15, 10, 15, 10)
        self.tabs.addTab(self.table_tab, "Match List")

        self.table = None
        self.canvas_widgets = []

        self.__load_stylesheet()

    # === Public Methods ===
    def clear_layout(self):
        """Completely clear old charts and table from the view."""
        # --- Remove all canvases (matplotlib) ---
        for w in self.canvas_widgets:
            w.setParent(None)
            w.deleteLater()
        self.canvas_widgets.clear()

        # --- Fully clear the scroll layout (chart area) ---
        def clear_layout_items(layout):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    child_layout = item.layout()
                    if widget is not None:
                        widget.deleteLater()
                    elif child_layout is not None:
                        clear_layout_items(child_layout)

        clear_layout_items(self.scroll_layout)

        # --- Clear the table tab content ---
        if self.table:
            self.table.setParent(None)
            self.table.deleteLater()
            self.table = None

    def refresh_view(self, data_list):
        self.clear_layout()

        if not data_list:
            self.scroll_layout.addWidget(QLabel("No prediction data available."))
            return

        df = pd.DataFrame(data_list)
        figures = self.__generate_figures(df)

        # Place charts in two columns
        col_layout = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        for i, (fig, desc) in enumerate(figures):
            canvas = FigureCanvas(fig)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            canvas.setMinimumHeight(400)

            frame = QFrame()
            frame.setObjectName("chartFrame")
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(12, 12, 12, 12)
            frame_layout.addWidget(canvas)

            # Description label under each chart
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setStyleSheet("color: white; font-size: 12px; margin-top: 8px;")
            frame_layout.addWidget(desc_label)

            if i % 2 == 0:
                left_col.addWidget(frame)
            else:
                right_col.addWidget(frame)

            self.canvas_widgets.append(canvas)

        col_layout.addLayout(left_col)
        col_layout.addLayout(right_col)
        self.scroll_layout.addLayout(col_layout)

        # Create match table
        self.table = self.__create_match_table(df)
        self.table_layout.addWidget(self.table)

    # === Internal Methods ===
    @staticmethod
    def __generate_figures(df: pd.DataFrame) -> list:
        figs = []

        # --- xG Distribution ---
        fig1, ax1 = plt.subplots()
        ax1.hist(df["home_xg"], bins=15, alpha=0.6, label="Home xG")
        ax1.hist(df["away_xg"], bins=15, alpha=0.6, label="Away xG")
        ax1.set_title("Distribution of Expected Goals")
        ax1.set_xlabel("xG")
        ax1.set_ylabel("Count")
        ax1.legend()
        figs.append((fig1, "Shows how expected goals (xG) are distributed across matches for home and away teams."))

        # --- Accuracy per Model ---
        valid_df = df[(df["real_home_score"] >= 0) & (df["real_away_score"] >= 0)].copy()
        if not valid_df.empty:
            def predicted_result(row):
                probs = {"Home": row["home_p"], "Draw": row["draw_p"], "Away": row["away_p"]}
                return max(probs, key=probs.get)

            def actual_result(row):
                if row["real_home_score"] > row["real_away_score"]:
                    return "Home"
                elif row["real_home_score"] < row["real_away_score"]:
                    return "Away"
                else:
                    return "Draw"

            valid_df["predicted"] = valid_df.apply(predicted_result, axis=1)
            valid_df["actual"] = valid_df.apply(actual_result, axis=1)
            valid_df["correct"] = valid_df["predicted"] == valid_df["actual"]

            accuracy = valid_df.groupby("model")["correct"].mean() * 100

            fig2, ax2 = plt.subplots()
            accuracy.plot(kind="bar", ax=ax2)
            ax2.set_title("Prediction Accuracy by Model")
            ax2.set_ylabel("Accuracy (%)")
            ax2.set_ylim(0, 100)
            for i, v in enumerate(accuracy):
                ax2.text(i, v + 1, f"{v:.1f}%", ha='center')
            figs.append((fig2, "Compares how accurate each prediction model was based on actual match outcomes."))
        else:
            fig2, ax2 = plt.subplots()
            ax2.text(0.5, 0.5, "No completed matches available for accuracy evaluation.",
                     ha="center", va="center", fontsize=12)
            ax2.axis("off")
            figs.append((fig2, "Accuracy data unavailable (no completed matches)."))

        # --- Probability Distributions ---
        fig3, ax3 = plt.subplots()
        ax3.hist(df["home_p"], bins=15, alpha=0.6, label="Home Win")
        ax3.hist(df["draw_p"], bins=15, alpha=0.6, label="Draw")
        ax3.hist(df["away_p"], bins=15, alpha=0.6, label="Away Win")
        ax3.set_title("Distribution of Predicted Probabilities")
        ax3.set_xlabel("Probability")
        ax3.set_ylabel("Count")
        ax3.legend()
        figs.append((fig3, "Displays how prediction probabilities are distributed for home, draw, and away outcomes."))

        # --- Average per Model ---
        fig4, ax4 = plt.subplots()
        model_avg = df.groupby("model")[["home_xg", "away_xg", "home_p", "draw_p", "away_p"]].mean()
        model_avg.plot(kind="bar", ax=ax4)
        ax4.set_title("Average Predictions per Model")
        ax4.set_ylabel("Mean Value")
        figs.append((fig4, "Shows average predicted values (xG and probabilities) for each model."))

        plt.tight_layout(rect=(0, 0, 1, 0.95))
        return figs

    @staticmethod
    def __create_match_table(df: pd.DataFrame) -> QTableWidget:
        table = QTableWidget()
        table.setObjectName("statsTable")

        headers = [
            "Match", "Model", "Home xG", "Away xG",
            "Home Win %", "Draw %", "Away Win %", "Result"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(df))

        for i, row in df.iterrows():
            match_text = f"{row['home_name']} vs {row['away_name']}"
            items = [
                QTableWidgetItem(match_text),
                QTableWidgetItem(row["model"]),
                QTableWidgetItem(f"{row['home_xg']:.2f}"),
                QTableWidgetItem(f"{row['away_xg']:.2f}"),
                QTableWidgetItem(f"{row['home_p'] * 100:.1f}%"),
                QTableWidgetItem(f"{row['draw_p'] * 100:.1f}%"),
                QTableWidgetItem(f"{row['away_p'] * 100:.1f}%")
            ]

            if row["real_home_score"] == -1 or row["real_away_score"] == -1:
                result = "⏳ Yet to play"
            else:
                result = f"{int(row['real_home_score'])} - {int(row['real_away_score'])}"
            items.append(QTableWidgetItem(result))

            for col, item in enumerate(items):
                if col == 1:
                    item.setToolTip("First model - XGB\nSecond model - MLP\n"
                                    "Third model - GradientBoost\nFourth model - SVR")
                else:
                    item.setToolTip(item.text())
                table.setItem(i, col, item)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        return table

    def __load_stylesheet(self):
        qss_path = resource_path("./qss/prediction_statistics.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
