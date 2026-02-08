from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from datetime import datetime
import os
from ResourcePath import resource_path


class TrainingEditView(QWidget):
    """
    GUI for configuring and training Support Vector Regression (SVR) models.

    Allows the user to:
        - Filter datasets by team name and year range
        - Adjust SVR parameters (C and Gamma) with beginner-friendly descriptions
        - Trigger model training with the 'Train / Update SVR' button

    Layout:
        - Top bar with Home button
        - Center content with:
            * Page title and subtitle
            * Dataset filters (team name, year range)
            * SVR parameter settings with detailed explanations
            * Train button at bottom

    Features:
        - Paired inputs (min/max) automatically synchronize to maintain valid ranges
        - Tip labels to guide the user
        - Values constrained to reasonable ranges for SVR parameters

    Styling:
        - Uses external QSS file located at "./qss/training_edit_view.qss"

    Signals:
        - No custom PyQt signals defined (buttons emit standard clicked signals)
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xGoalPro - Train Models")
        self.setObjectName("TrainingEditView")

        # === MAIN WRAPPER LAYOUT ===
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(20)

        # === TOP BAR (Home button on the left) ===
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignLeft)

        self.home_button = QPushButton("🏠 Home")
        self.home_button.setObjectName("secondaryButton")

        top_bar.addWidget(self.home_button)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)

        # === CENTER CONTENT ===
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(40)

        # Title and Subtitle
        title_label = QLabel("Train Support Vector Regression (SVR) Models")
        title_label.setObjectName("pageTitle")

        subtitle_label = QLabel("Set filters and adjust model settings below.")
        subtitle_label.setObjectName("pageSubtitle")

        center_layout.addWidget(title_label, alignment=Qt.AlignCenter)
        center_layout.addWidget(subtitle_label, alignment=Qt.AlignCenter)

        # === FORM SECTION ===
        form = QFormLayout()
        form.setFormAlignment(Qt.AlignCenter)
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(20)

        current_year = datetime.now().year

        # --- Dataset Filters Section ---
        filter_label = QLabel("Dataset Filters")
        filter_label.setObjectName("sectionLabel")
        form.addRow(filter_label)

        filter_desc = QLabel(
            "Select which football data you want to use for training. "
            "You can focus on one team or include all matches from a range of years."
        )
        filter_desc.setWordWrap(True)
        filter_desc.setStyleSheet("color: #e0e1dd; font-size: 16px;")
        form.addRow(filter_desc)

        self.team_input = QLineEdit()
        self.team_input.setPlaceholderText("Leave empty to include all teams (e.g., Real Madrid)")
        form.addRow("Team name:", self.team_input)

        self.year_from = QSpinBox()
        self.year_from.setRange(2005, current_year)
        self.year_from.setValue(2015)

        self.year_to = QSpinBox()
        self.year_to.setRange(2005, current_year)
        self.year_to.setValue(current_year)

        year_layout = QHBoxLayout()
        year_layout.addWidget(self.year_from)
        year_layout.addWidget(self.year_to)
        form.addRow("Match date year (from - to):", year_layout)

        form.addRow(QLabel(""))

        # --- SVR Parameters Section ---
        svr_label = QLabel("Support Vector Regression (SVR) Settings")
        svr_label.setObjectName("sectionLabel")
        form.addRow(svr_label)

        # Beginner-friendly description
        svr_desc = QLabel(
            "These settings control how the computer learns from the data.\n\n"
            "C (Complexity): Think of this as how strictly the model tries to fit past data. "
            "Smaller values make it simpler but less precise, while larger values make it fit the data more closely.\n\n"
            "Gamma (Sensitivity): This controls how far the model looks around each data point. "
            "Smaller values mean the model looks at a wider picture (smoother predictions), "
            "while larger values make it focus more closely on each data point (more detailed but can overfit)."
        )
        svr_desc.setWordWrap(True)
        svr_desc.setStyleSheet("color: #e0e1dd; font-size: 16px;")
        form.addRow(svr_desc)

        # SVR parameter ranges
        self.c_min = QDoubleSpinBox()
        self.c_min.setRange(0.001, 1000.0)
        self.c_min.setValue(0.1)
        self.c_min.setToolTip("Lower value = simpler model, less accurate; higher = more precise but may overfit.")

        self.c_max = QDoubleSpinBox()
        self.c_max.setRange(0.001, 1000.0)
        self.c_max.setValue(10.0)
        self.c_max.setToolTip("Upper value = how complex the model is allowed to be.")

        self.gamma_min = QDoubleSpinBox()
        self.gamma_min.setRange(0.0001, 1.0)
        self.gamma_min.setValue(0.001)
        self.gamma_min.setToolTip("Lower value = smoother predictions, less detail.")

        self.gamma_max = QDoubleSpinBox()
        self.gamma_max.setRange(0.0001, 1.0)
        self.gamma_max.setValue(0.1)
        self.gamma_max.setToolTip("Higher value = more detail, but can overfit to training data.")

        c_layout = QHBoxLayout()
        c_layout.addWidget(self.c_min)
        c_layout.addWidget(self.c_max)
        form.addRow("C range (from - to):", c_layout)

        gamma_layout = QHBoxLayout()
        gamma_layout.addWidget(self.gamma_min)
        gamma_layout.addWidget(self.gamma_max)
        form.addRow("Gamma range (from - to):", gamma_layout)

        center_layout.addLayout(form)

        # === Train Button ===
        self.train_button = QPushButton("Train / Update SVR")
        self.train_button.setObjectName("primaryButton")
        center_layout.addWidget(self.train_button, alignment=Qt.AlignCenter)

        # Add stretch for vertical centering
        main_layout.addStretch()
        main_layout.addLayout(center_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # === Value Constraints Between Paired Inputs ===
        self.year_from.valueChanged.connect(lambda _: self.sync_min_max(self.year_from, self.year_to))
        self.year_to.valueChanged.connect(lambda _: self.sync_min_max(self.year_from, self.year_to))
        self.c_min.valueChanged.connect(lambda _: self.sync_min_max(self.c_min, self.c_max))
        self.c_max.valueChanged.connect(lambda _: self.sync_min_max(self.c_min, self.c_max))
        self.gamma_min.valueChanged.connect(lambda _: self.sync_min_max(self.gamma_min, self.gamma_max))
        self.gamma_max.valueChanged.connect(lambda _: self.sync_min_max(self.gamma_min, self.gamma_max))

        # === Load QSS ===
        qss_path = resource_path("./qss/training_edit_view.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def sync_min_max(self, min_widget, max_widget):
        """Ensure that the 'min' value is never greater than the 'max' value."""
        min_val = min_widget.value()
        max_val = max_widget.value()

        if min_val > max_val:
            sender = self.sender()
            if sender == min_widget:
                max_widget.setValue(min_val)
            else:
                min_widget.setValue(max_val)
