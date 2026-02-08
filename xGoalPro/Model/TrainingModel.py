from PyQt5.QtCore import QObject, pyqtSignal
import pandas as pd
import numpy as np
import joblib
from difflib import get_close_matches
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error
import os
from typing import Optional, Any, Tuple
from ResourcePath import resource_path


class TrainingModel(QObject):
    """Model for training Support Vector Regression (SVR) models for football match scores.

    This model uses a historical dataset to train SVR models for predicting home and away goals.
    It emits signals to notify the UI about log messages and training completion status.

    Signals:
        log_message (str): Emitted with status messages during training.
        training_finished (bool, str): Emitted when training finishes or fails, with success flag and message.

    Attributes:
        __dataset_path (str): Path to the CSV dataset.
        __scaler_path (str): Path to the pre-fitted scaler (must exist).
        scaler (sklearn.preprocessing.StandardScaler): Pre-loaded scaler used for feature normalization.
    """

    log_message = pyqtSignal(str)
    training_finished = pyqtSignal(bool, str)

    def __init__(self, dataset_path: str, scaler_path: str):
        """Initialize the TrainingModel with dataset and scaler paths.

        Args:
            dataset_path (str): Path to CSV dataset containing match and team features.
            scaler_path (str): Path to pre-fitted scaler (used for feature normalization).

        Raises:
            FileNotFoundError: If the scaler file does not exist at the given path.
        """
        super().__init__()
        self.__dataset_path: str = dataset_path
        self.__scaler_path: str = scaler_path

        # Load existing scaler (never re-fit)
        if os.path.exists(resource_path(self.__scaler_path)):
            self.scaler = joblib.load(resource_path(self.__scaler_path))
        else:
            raise FileNotFoundError(f"Scaler not found at: {self.__scaler_path}")

        self.__features = [
            "HomeElo", "AwayElo",
            "Home_Last5_Points", "Home_Last5_GoalsFor", "Home_Last5_GoalsAgainst",
            "Home_Last5_Wins", "Home_Last5_Draws", "Home_Last5_Losses",
            "Away_Last5_Points", "Away_Last5_GoalsFor", "Away_Last5_GoalsAgainst",
            "Away_Last5_Wins", "Away_Last5_Draws", "Away_Last5_Losses"
        ]

        self.__label_home = "FTHome"
        self.__label_away = "FTAway"

        self.__home_model_path = "./Assets/models/home_svr.pkl"
        self.__away_model_path = "./Assets/models/away_svr.pkl"

    # --- Train SVR Models ---
    def train_svr(self, team_name: str, year_from: int, year_to: int, param_ranges: dict) -> Optional[Tuple[bool, Any]]:
        """Train Support Vector Regression (SVR) models for home and away goals.

        Filters the dataset by team name and year range, applies a pre-fitted scaler,
        splits data into train/test sets, performs randomized hyperparameter search,
        trains SVR models, calculates MAE, and saves the trained models to disk.

        Args:
            team_name (str): Name of the team to filter dataset. Uses closest match if exact name not found.
            year_from (int): Start year for filtering matches.
            year_to (int): End year for filtering matches.
            param_ranges (dict): Dictionary specifying min/max ranges for SVR hyperparameters 'C' and 'gamma'.

        Returns:
            Optional[Tuple[bool, Any]]: None (results are communicated via signals). TrainingFinished signal emits:
                - success (bool): True if training completed successfully.
                - message (str): Details of training result or failure.
        """
        try:
            df = self.__filter_dataset(team_name, year_from, year_to)
            if df.empty:
                self.training_finished.emit(False, "Filtered dataset is empty — no training performed.")
                return

            x = df[self.__features]
            y_home = df[self.__label_home]
            y_away = df[self.__label_away]

            # Use existing scaler (do not re-fit)
            x_scaled = self.scaler.transform(x)
            self.log_message.emit("Scaler loaded and applied (not updated).")

            x_train, x_test, y_train_home, y_test_home = (
                train_test_split(x_scaled, y_home, test_size=0.2, random_state=42))
            _, _, y_train_away, y_test_away = (
                train_test_split(x_scaled, y_away, test_size=0.2, random_state=42))

            param_grid = {
                "C": np.linspace(param_ranges["C_min"], param_ranges["C_max"], 5).tolist(),
                "gamma": np.linspace(param_ranges["gamma_min"], param_ranges["gamma_max"], 5).tolist(),
                "kernel": ["rbf"]
            }

            # --- Train Home SVR ---
            self.log_message.emit("Training Home SVR...")
            home_svr = SVR()
            search_home = RandomizedSearchCV(home_svr, param_distributions=param_grid, n_iter=10, cv=3, n_jobs=1)
            search_home.fit(x_train, y_train_home)
            best_home = search_home.best_estimator_
            mae_home = mean_absolute_error(y_test_home, best_home.predict(x_test))
            self.log_message.emit(f"Home SVR MAE: {mae_home:.3f}")
            joblib.dump(best_home, resource_path(self.__home_model_path))

            # --- Train Away SVR ---
            self.log_message.emit("Training Away SVR...")
            away_svr = SVR()
            search_away = RandomizedSearchCV(away_svr, param_distributions=param_grid, n_iter=10, cv=3, n_jobs=1)
            search_away.fit(x_train, y_train_away)
            best_away = search_away.best_estimator_
            mae_away = mean_absolute_error(y_test_away, best_away.predict(x_test))
            self.log_message.emit(f"Away SVR MAE: {mae_away:.3f}")
            joblib.dump(best_away, resource_path(self.__away_model_path))

            self.training_finished.emit(
                True, f"SVR updated successfully. (MAE Home={mae_home:.3f}, Away={mae_away:.3f})")

        except Exception as e:
            self.training_finished.emit(False, f"Training failed: {str(e)}")

    # --- Filter dataset based on team and year ---
    def __filter_dataset(self, team_name: str, year_from: int, year_to: int) -> Optional[pd.DataFrame]:
        """Filter the dataset by team name and year, and drop rows with missing values.

        Args:
            team_name (str): Name of the team to filter dataset. Closest match used if exact name not found.
            year_from (int): Start year for filtering matches.
            year_to (int): End year for filtering matches.

        Returns:
            pd.DataFrame: Filtered DataFrame containing only relevant matches with no missing values
                          in features or labels.
        """
        df = pd.read_csv(resource_path(self.__dataset_path), low_memory=False)
        df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")
        df = df.dropna(subset=["MatchDate"])
        df = df[(df["MatchDate"].dt.year >= year_from) & (df["MatchDate"].dt.year <= year_to)]

        if team_name.strip():
            all_teams = pd.concat([df["HomeTeam"], df["AwayTeam"]]).unique().tolist()
            match = get_close_matches(team_name, all_teams, n=1, cutoff=0.4)
            if match:
                team = match[0]
                df = df[(df["HomeTeam"] == team) | (df["AwayTeam"] == team)]
                self.log_message.emit(f"Filtered dataset for team: {team}")
            else:
                self.log_message.emit(f"No close match found for '{team_name}', using full dataset.")
        else:
            self.log_message.emit("No team specified — using full dataset.")

        # Drop rows with any missing feature or label
        before_drop = len(df)
        df = df.dropna(subset=self.__features + [self.__label_home, self.__label_away])
        after_drop = len(df)
        self.log_message.emit(f"Dropped {before_drop - after_drop} rows with NaN values. Remaining: {after_drop}")

        return df
