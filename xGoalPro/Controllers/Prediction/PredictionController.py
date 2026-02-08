from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget

from qasync import asyncSlot

from View.Components.LoadingWidget import LoadingWidget

from View.Prediction.LeagueHubView import LeagueHubView
from View.Prediction.TeamHubView import TeamHubView
from View.Prediction.MatchHubView import MatchHubView
from View.Prediction.MatchView import MatchView
from Model.PredictionModel import PredictionModel

from ResourcePath import resource_path


class PredictionController(QObject):
    """
    Controller for the Prediction module.

    Manages interactions between the PredictionModel and the UI views
    (LeagueHubView, TeamHubView, MatchHubView, MatchView). Handles
    asynchronous fetching of leagues, teams, matches, head-to-head data,
    and score predictions. Updates the UI via signals and loading widgets.

    Signals:
        return_to_home (pyqtSignal): Emitted to navigate back to the main home screen.
        switch_to_view (pyqtSignal[QWidget]): Emitted to switch the currently displayed view.
        error_occurred (pyqtSignal[list]): Emitted when an error occurs, passing a list of error messages.
        information (pyqtSignal[list]): Emitted for general informational messages.
    
    Attributes:
        __model (PredictionModel): The prediction model handling data fetching and predictions.
        __league_view (LeagueHubView): View for selecting leagues.
        __team_view (TeamHubView): View for selecting teams.
        __matches_view (MatchHubView): View for selecting matches.
        __match_view (MatchView): View displaying match predictions and results.
    """
    return_to_home: pyqtSignal = pyqtSignal()
    switch_to_view: pyqtSignal(QWidget) = pyqtSignal(QWidget)
    error_occurred: pyqtSignal(list) = pyqtSignal(list)
    information: pyqtSignal(list) = pyqtSignal(list)

    def __init__(self, model, league_view, team_view, matches_view, match_view):
        """
        Initialize the controller with model and views, and setup connections.

        Args:
            model (PredictionModel): The prediction model.
            league_view (LeagueHubView): League selection UI.
            team_view (TeamHubView): Team selection UI.
            matches_view (MatchHubView): Match selection UI.
            match_view (MatchView): Match prediction and details UI.
        """
        super().__init__()

        self.__model: PredictionModel = model
        self.__league_view: LeagueHubView = league_view
        self.__team_view: TeamHubView = team_view
        self.__matches_view: MatchHubView = matches_view
        self.__match_view: MatchView = match_view

        self.__init_connections()

    async def cleanup(self) -> None:
        """
        Clean up all view widgets and release model resources asynchronously.
        """
        self.__league_view.deleteLater()
        self.__team_view.deleteLater()
        self.__matches_view.deleteLater()
        self.__match_view.deleteLater()
        await self.__model.cleanup()
        self.__model = None

    @asyncSlot()
    async def fetch_league(self) -> bool:
        """
        Fetch leagues asynchronously from the model and update the league view.

        Shows a loading widget while fetching. Emits errors via the error_occurred
        signal and navigates back to home if fetching fails.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching leagues...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_leagues()
            if success:

                self.__refresh_league_view(data)
                return True

            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()
                return False
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
            return False
        finally:
            loading.deleteLater()

    @asyncSlot(str)
    async def __fetch_teams(self, league_code: str) -> None:
        """
        Fetch teams for a given league asynchronously.

        Args:
            league_code (str): The league code to fetch teams for.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching teams...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_teams(league_code)
            if success:

                self.__refresh_team_view(data)

            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    @asyncSlot(int)
    async def __fetch_matches(self, team_code: int) -> None:
        """
        Fetch matches for a given team asynchronously.

        Args:
            team_code (int): The ID of the team to fetch matches for.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching matches...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_matches(team_code)
            if success:

                self.__refresh_matches_view(data)

            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    @asyncSlot(dict)
    async def __show_match_and_fetch_h2h(self, match_data: dict) -> None:
        """
        Fetch head-to-head data for a match and update the match view.

        Args:
            match_data (dict): Dictionary containing match information including ID.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching head2head...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_h2h(match_data['id'])

            if success:
                self.__refresh_match_prediction_view([match_data], data[0], data[1])
            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()

        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    @asyncSlot(int, int, int, list)
    async def __predict_match_score(self, home_id: int, away_id: int, match_id: int, code: list) -> None:
        """
        Predict the score for a match using selected models.

        Args:
            home_id (int): Home team ID.
            away_id (int): Away team ID.
            match_id (int): Match ID.
            code (list): List of model selection flags (1 for selected, 0 for not selected).
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Predicting score...")
        self.switch_to_view.emit(loading)
        try:

            success, data = await self.__model.predict_scores(home_id, away_id, match_id, code)

            if success:
                self.__refresh_result(data)
            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()

        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    def __refresh_league_view(self, league_data: list) -> None:
        """
        Refresh the league view with fetched data and switch to it.

        Args:
            league_data (list): List of league dictionaries with info and emblems.
        """
        self.__league_view.refresh_view(league_data)
        self.switch_to_view.emit(self.__league_view)

    def __refresh_team_view(self, team_data: tuple) -> None:
        """
        Refresh the team view with fetched data and switch to it.

        Args:
            team_data (tuple): Tuple containing teams and competition name.
        """
        self.__team_view.refresh_view(team_data)
        self.switch_to_view.emit(self.__team_view)

    def __refresh_matches_view(self, match_data: list) -> None:
        """
        Refresh the matches view with fetched match data and switch to it.

        Args:
            match_data (list): List of match dictionaries with basic info.
        """
        self.__matches_view.refresh_view(match_data)
        self.switch_to_view.emit(self.__matches_view)

    def __refresh_match_prediction_view(self, data: list, h2h_data: list, ml_models: dict) -> None:
        """
        Refresh the match view with match details, head-to-head data, and ML models.

        Args:
            data (list): List containing the match details.
            h2h_data (list): Head-to-head match data.
            ml_models (dict): ML models used for prediction.
        """
        self.__match_view.refresh_view(data, h2h_data, ml_models)
        self.switch_to_view.emit(self.__match_view)

    def __refresh_result(self, data: dict) -> None:
        """
        Refresh the match view with the prediction result.

        Args:
            data (dict): Dictionary containing prediction results.
        """
        self.__match_view.refresh_result(data)
        self.switch_to_view.emit(self.__match_view)

    def __init_connections(self) -> None:
        """
        Connect signals from all views to the appropriate slots in the controller.

        Handles navigation and user actions such as selecting leagues, teams,
        matches, and performing predictions.
        """
        self.__league_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__league_view.show_league.connect(lambda code: self.__fetch_teams(code))

        self.__team_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__team_view.back_to_league_hub.connect(lambda: self.switch_to_view.emit(self.__league_view))
        self.__team_view.show_team.connect(lambda code: self.__fetch_matches(code))

        self.__matches_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__matches_view.back_to_league_hub.connect(lambda: self.switch_to_view.emit(self.__league_view))
        self.__matches_view.back_to_team_hub.connect(lambda: self.switch_to_view.emit(self.__team_view))
        self.__matches_view.show_match.connect(lambda data: self.__show_match_and_fetch_h2h(data))

        self.__match_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__match_view.back_to_league_hub.connect(lambda: self.switch_to_view.emit(self.__league_view))
        self.__match_view.back_to_team_hub.connect(lambda: self.switch_to_view.emit(self.__team_view))
        self.__match_view.back_to_match_hub.connect(lambda: self.switch_to_view.emit(self.__matches_view))
        self.__match_view.predict_match.connect(
            lambda home_id, away_id, match_id, code: self.__predict_match_score(home_id, away_id, match_id, code))
        self.__match_view.no_model_selected.connect(lambda: self.error_occurred.emit(["Please select at least one model for the prediction!"]))
