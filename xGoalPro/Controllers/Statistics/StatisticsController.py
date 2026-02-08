from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget
from qasync import asyncSlot

from View.Components.LoadingWidget import LoadingWidget
from View.Statistics.IndexView import StatisticsIndexView
from View.Statistics.StatisticsLeagueHubView import StatisticsLeagueHubView
from View.Statistics.StatisticsLeagueView import StatisticsLeagueView
from View.Statistics.StatisticsTeamView import StatisticsTeamView
from View.Statistics.PredictionStatisticsView import PredictionStatisticsView

from ResourcePath import resource_path


class StatisticsController(QObject):
    """
    Controller for the Statistics module.

    Manages interactions between the StatisticsModel and the UI views
    (StatisticsIndexView, StatisticsLeagueHubView, StatisticsLeagueView, 
    StatisticsTeamView, PredictionStatisticsView). Handles asynchronous 
    fetching of league, team, and prediction statistics, updating the UI 
    via signals and loading widgets.

    Signals:
        return_to_home (pyqtSignal): Emitted to navigate back to the main home screen.
        switch_to_view (pyqtSignal[QWidget]): Emitted to switch the currently displayed view.
        error_occurred (pyqtSignal[list]): Emitted when an error occurs, passing a list of error messages.
        information (pyqtSignal[list]): Emitted for general informational messages.
    
    Attributes:
        __model (StatisticsModel): The statistics model handling data fetching.
        __index_view (StatisticsIndexView): The main index view of statistics module.
        __league_hub_view (StatisticsLeagueHubView): View displaying all leagues.
        __league_view (StatisticsLeagueView): View displaying a specific league's statistics.
        __team_view (StatisticsTeamView): View displaying a specific team's statistics.
        __prediction_stats_view (PredictionStatisticsView): View displaying prediction statistics.
    """
    return_to_home: pyqtSignal = pyqtSignal()
    switch_to_view: pyqtSignal(QWidget) = pyqtSignal(QWidget)
    error_occurred: pyqtSignal(list) = pyqtSignal(list)
    information: pyqtSignal(list) = pyqtSignal(list)
    
    def __init__(self, model, index_view, league_hub_view, league_view, team_view, prediction_stats_view):
        """
        Initialize the controller with the model and all statistics views, 
        and setup the signal-slot connections.

        Args:
            model (StatisticsModel): The statistics model.
            index_view (StatisticsIndexView): The main index UI.
            league_hub_view (StatisticsLeagueHubView): League hub UI.
            league_view (StatisticsLeagueView): League statistics UI.
            team_view (StatisticsTeamView): Team statistics UI.
            prediction_stats_view (PredictionStatisticsView): Prediction statistics UI.
        """
        super().__init__()
        self.__model = model
        self.__index_view: StatisticsIndexView = index_view
        self.__league_hub_view: StatisticsLeagueHubView = league_hub_view
        self.__league_view: StatisticsLeagueView = league_view
        self.__team_view: StatisticsTeamView = team_view
        self.__prediction_stats_view: PredictionStatisticsView = prediction_stats_view

        self.__init_connections()

    async def cleanup(self) -> None:
        """
        Clean up all view widgets and release model resources asynchronously.
        """
        self.__index_view.deleteLater()
        self.__league_hub_view.deleteLater()
        self.__league_view.deleteLater()
        self.__team_view.deleteLater()
        self.__prediction_stats_view.deleteLater()
        await self.__model.cleanup()
        self.__model = None

    def __init_connections(self) -> None:
        """
        Connect signals from all views to appropriate slots in the controller.

        Handles navigation and user actions such as selecting leagues, teams,
        and fetching predictions.
        """
        self.__index_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__index_view.team_stats_btn_clicked.connect(lambda: self.__fetch_league())
        self.__index_view.prediction_statistics_btn_clicked.connect(lambda: self.__fetch_predictions())

        self.__league_hub_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__league_hub_view.back_to_index.connect(lambda: self.switch_to_view.emit(self.__index_view))
        self.__league_hub_view.show_league.connect(lambda league: self.__fetch_league_data(league))

        self.__league_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__league_view.back_to_index.connect(lambda: self.switch_to_view.emit(self.__index_view))
        self.__league_view.back_to_league_hub.connect(lambda: self.switch_to_view.emit(self.__league_hub_view))
        self.__league_view.team_clicked.connect(lambda team: self.__fetch_team_data(team))

        self.__team_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__team_view.back_to_index.connect(lambda: self.switch_to_view.emit(self.__index_view))
        self.__team_view.back_to_league_hub.connect(lambda: self.switch_to_view.emit(self.__league_hub_view))
        self.__team_view.back_to_league.connect(lambda: self.switch_to_view.emit(self.__league_view))

        self.__prediction_stats_view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.__prediction_stats_view.back_to_index.connect(lambda: self.switch_to_view.emit(self.__index_view))

    @asyncSlot()
    async def __fetch_league(self) -> None:
        """
        Fetch all leagues asynchronously and update the league hub view.

        Shows a loading widget while fetching. Emits errors via the error_occurred
        signal and navigates back to home if fetching fails.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching leagues...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_leagues()
            if success:

                self.__refresh_league_hub_view(data)

            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    @asyncSlot(str)
    async def __fetch_league_data(self, league: str) -> None:
        """
        Fetch detailed statistics for a specific league asynchronously.

        Args:
            league (str): The league code or identifier.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching league data...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_league_statistics(league)
            if success:

                self.__refresh_league_view(data)

            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    @asyncSlot(str)
    async def __fetch_team_data(self, team: int) -> None:
        """
        Fetch detailed statistics for a specific team asynchronously.

        Args:
            team (str): The team code or identifier.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching team data ...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_team_statistics(team)
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

    @asyncSlot()
    async def __fetch_predictions(self) -> None:
        """
        Fetch prediction statistics asynchronously.

        Updates the PredictionStatisticsView when fetching is successful.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching predictions ...")
        self.switch_to_view.emit(loading)
        try:
            success, data = await self.__model.fetch_predictions()
            if success:

                self.__refresh_prediction_statistics_view(data)

            else:
                self.error_occurred.emit(data)
                self.return_to_home.emit()
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.return_to_home.emit()
        finally:
            loading.deleteLater()

    def __refresh_league_hub_view(self, data: list) -> None:
        """
        Refresh the league hub view with fetched data and switch to it.

        Args:
            data (list): List of league dictionaries.
        """
        self.__league_hub_view.refresh_view(data)
        self.switch_to_view.emit(self.__league_hub_view)

    def __refresh_league_view(self, data: list) -> None:
        """
        Refresh a specific league view with fetched data and switch to it.

        Args:
            data (list): List of league statistics data.
        """
        self.__league_view.refresh_view(data)
        self.switch_to_view.emit(self.__league_view)

    def __refresh_team_view(self, data: list) -> None:
        """
        Refresh a specific team view with fetched data and switch to it.

        Args:
            data (list): List of team statistics data.
        """
        self.__team_view.refresh_view(data)
        self.switch_to_view.emit(self.__team_view)

    def __refresh_prediction_statistics_view(self, data: list) -> None:
        """
        Refresh the prediction statistics view with fetched data and switch to it.

        Args:
            data (list): List of prediction statistics data.
        """
        self.__prediction_stats_view.refresh_view(data)
        self.switch_to_view.emit(self.__prediction_stats_view)
