import asyncio

from qasync import asyncSlot
import gc


from Controllers.Prediction.PredictionController import PredictionController
from Controllers.Statistics.StatisticsController import StatisticsController
from Controllers.Minigame.AuthController import AuthController
from Controllers.Minigame.HubController import HubController
from Controllers.Minigame.FUTController import FUTController
from Controllers.Minigame.RiskGameController import RiskGameController
from Controllers.Minigame.SnakeController import SnakeController
from Controllers.Minigame.MineSweeperController import MineSweeperController
from Controllers.Minigame.DribbleKingController import DribbleKingController
from Controllers.Minigame.ReflexGameController import ReflexGameController
from Controllers.Training.TrainingController import TrainingController

from Persistence.SQLiteUserStorage import SQLiteUserStorage
from Persistence.SQLiteCollectionStorage import SQLiteCollectionStorage
from Persistence.SQLiteRiskGameStorage import SQLiteRiskGameStorage
from Persistence.SQLiteSnakeGameStorage import SQLiteSnakeGameStorage
from Persistence.SQLiteDribbleKingStorage import SQLiteDribbleKingStorage
from Persistence.SQLitePredictionStorage import SQLitePredictionStorage
from Persistence.Api import FutApi, PredictionApi
from Persistence.DataLoader import IDataLoader, StatisticsDataLoader

from Model.Auth import IAuthModel, AuthModel
from Model.FUTModel import FUTModel
from Model.RiskGameModel import RiskGameModel
from Model.SnakeGameModel import SnakeGameModel
from Model.DribbleKingModel import DribbleKingModel
from Model.DummyModel import DummyModel
from Model.ReflexGameModel import ReflexGameModel
from Model.PredictionModel import PredictionModel
from Model.StatisticsModel import StatisticsModel
from Model.TrainingModel import TrainingModel

from View.Components.MessageBoxes import ErrorMessageBox, InfoMessageBox
from View.HomeWindow import HomeWindow
from View.Login_Register.Login import LoginPage
from View.Login_Register.Register import RegisterPage
from View.Minigame.MinigameHub import MiniGameHubView
from View.Minigame.FUTView import FUTMainView
from View.Minigame.RiskGameView import RiskGameView
from View.Minigame.SnakeView import SnakeGameView
from View.Minigame.MineSweeperView import MineSweeperView
from View.Minigame.DribbleKingView import DribbleKingView
from View.Minigame.ReflexGameView import ReflexGameView
from View.Prediction.LeagueHubView import LeagueHubView
from View.Prediction.TeamHubView import TeamHubView
from View.Prediction.MatchHubView import MatchHubView
from View.Prediction.MatchView import MatchView
from View.Statistics.IndexView import StatisticsIndexView
from View.Statistics.StatisticsLeagueHubView import StatisticsLeagueHubView
from View.Statistics.StatisticsLeagueView import StatisticsLeagueView
from View.Statistics.StatisticsTeamView import StatisticsTeamView
from View.Statistics.PredictionStatisticsView import PredictionStatisticsView
from View.Training.TrainingEditView import TrainingEditView
from View.Training.TrainingLoadingView import TrainingLoadingView


from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon

from ResourcePath import resource_path


class App:
    """
    Central application coordinator that initializes and manages all major components:
    - Persistence layers
    - Models
    - Views
    - Controllers
    - UI navigation logic

    The class acts as the entry point for the entire system, responsible for wiring
    dependencies and switching between application modules (Minigames, Predictions,
    Statistics, and Training).

    It follows a Model-View-Controller (MVC) architecture with asynchronous
    initialization for database-backed components.
    """

    def __init__(self):
        """
        Initialize the main application instance.

        Sets up all persistence storages, models, views, and controllers.
        Establishes signal connections between UI and business logic and
        asynchronously prepares persistence layers for use.

        Side effects:
            - Opens main application window (`HomeWindow`).
            - Initializes all modules and signal bindings.
            - Schedules database connection setup via asyncio.

        Raises:
            Exception: If any critical initialization component fails.
        """
        # Persistence
        self.user_storage: SQLiteUserStorage = SQLiteUserStorage("./Assets/users.db")

        self.prediction_api: PredictionApi = PredictionApi(
            "http://api.football-data.org/v4", {"X-Auth-Token": "0ae181e65f9a4cc2aff8cc7ea67ff169"})
        self.prediction_storage: SQLitePredictionStorage = SQLitePredictionStorage("./Assets/predictions.db")

        self.statistics_data_loader: IDataLoader = StatisticsDataLoader("2025")

        # Models
        self.auth_model: IAuthModel = AuthModel(self.user_storage)

        ml_models: dict = {
            "XGB": (
                [
                    "./Assets/models/home_xgb.pkl",
                    "./Assets/models/away_xgb.pkl"
                ],
                (
                    "<b>XGBoost (Extreme Gradient Boosting)</b><br>"
                    "XGBoost is a tree-based ensemble model that combines many small decision trees.<br>"
                    "It learns patterns in data like shots, positions, and passes to predict how likely a team is to score (xG).<br>"
                    "<i>It’s fast, powerful, and works great for structured sports data such as match statistics.</i>"
                )
            ),

            "MLP": (
                [
                    "./Assets/models/home_mlp.pkl",
                    "./Assets/models/away_mlp.pkl"
                ],
                (
                    "<b>MLP (Multilayer Perceptron)</b><br>"
                    "A basic form of neural network that learns non-linear patterns between inputs and outcomes.<br>"
                    "For xG prediction, it can detect deeper relationships like player combinations, shot angles, and defensive gaps.<br>"
                    "<i>It’s flexible and can adapt to many kinds of features, but needs careful tuning.</i>"
                )
            ),

            "GradientBoost": (
                [
                    "./Assets/models/home_gradient_boosting.pkl",
                    "./Assets/models/away_gradient_boosting.pkl"
                ],
                (
                    "<b>Gradient Boosting Regressor</b><br>"
                    "Another ensemble of decision trees that learns sequentially — each new tree fixes the errors of the previous ones.<br>"
                    "For football xG, it’s great at capturing subtle relationships in historical shot data or player stats.<br>"
                    "<i>It’s slower than XGBoost but easier to understand for beginners.</i>"
                )
            ),

            "SVR": (
                [
                    "./Assets/models/home_svr.pkl",
                    "./Assets/models/away_svr.pkl"
                ],
                (
                    "<b>SVR (Support Vector Regressor)</b><br>"
                    "SVR tries to fit a line (or curve) that predicts continuous outcomes while ignoring small errors.<br>"
                    "For xG prediction, it estimates the expected goals by finding stable patterns across matches.<br>"
                    "<i>It’s simple and stable, but doesn’t always perform well on very large or noisy datasets.</i>"
                )
            )
        }


        self.prediction_model: PredictionModel = (
            PredictionModel(self.prediction_api, self.prediction_storage, ml_models))

        self.statistics_model = StatisticsModel(
            self.prediction_api, self.statistics_data_loader, self.prediction_storage)

        self.training_model = TrainingModel(
            "./Assets/models/dataset.csv", "./Assets/models/scaler.pkl")

        # Views
        self.home_window: HomeWindow = HomeWindow()

        self.prediction_league_view = LeagueHubView()
        self.prediction_team_view = TeamHubView()
        self.prediction_matches_view = MatchHubView()
        self.prediction_match_view = MatchView()

        self.statistics_league_hub_view = StatisticsLeagueHubView()
        self.statistics_index_view = StatisticsIndexView()
        self.statistics_league_view = StatisticsLeagueView()
        self.statistics_team_view = StatisticsTeamView()
        self.prediction_statistics_view = PredictionStatisticsView()

        self.login_page: LoginPage = LoginPage()
        self.register_page: RegisterPage = RegisterPage()

        self.minigame_hub_view: MiniGameHubView = MiniGameHubView("", -1, [])

        self.training_edit_view = TrainingEditView()
        self.training_loading_view = TrainingLoadingView()

        # Controllers
        self.auth_controller = AuthController(self.user_storage, self.auth_model, self.login_page, self.register_page)
        self.hub_controller = HubController(self.minigame_hub_view)

        self.prediction_controller: PredictionController = PredictionController(
            self.prediction_model, self.prediction_league_view, self.prediction_team_view,
            self.prediction_matches_view, self.prediction_match_view)

        self.statistics_controller = StatisticsController(
            self.statistics_model, self.statistics_index_view, self.statistics_league_hub_view,
            self.statistics_league_view, self.statistics_team_view, self.prediction_statistics_view)

        self.training_controller = TrainingController(self.training_model, self.training_edit_view,
                                                      self.training_loading_view)

        # Current Window
        self.current_window: QWidget = self.home_window
        self.current_window.setWindowIcon(QIcon(resource_path("./Assets/icon.ico")))

        # HomeWindow signals
        self.home_window.switch_to_minigame.connect(lambda: self.auth_controller.switch_to_log())
        self.home_window.switch_to_prediction.connect(lambda: self.__switch_to_prediction())
        self.home_window.switch_to_statistics.connect(lambda: self.__switch_to_statistics())
        self.home_window.switch_to_training.connect(lambda: self.__switch_to_training())

        self.__initialize_prediction()

        self.__initialize_statistics()

        self.__init_minigame_connections()
        asyncio.ensure_future(self.__initialize_persistence())

        self.home_window.showMaximized()

    async def close_app(self) -> None:
        """
        Gracefully shuts down the application and cleans up resources.

        Ensures that all controllers complete any ongoing asynchronous operations
        before application termination.
        """
        await self.auth_controller.cleanup()
        await self.hub_controller.cleanup()
        await self.prediction_controller.cleanup()
        await self.statistics_controller.cleanup()

    def show_new_window(self, window: QWidget) -> None:
        """
        Switch the currently visible window to a new one.

        Args:
            window (QWidget): The new window to display.

        Behavior:
            - Hides the current window if one is active.
            - Sets a standard application icon.
            - Displays the new window maximized (except for smaller minigame views).
        """
        if self.current_window:
            self.current_window.hide()
        self.current_window = window
        self.current_window.setWindowIcon(QIcon(resource_path("./Assets/icon.ico")))
        if isinstance(window, DribbleKingView) or isinstance(window, ReflexGameView):
            self.current_window.show()
        else:
            self.current_window.showMaximized()

    def hide_current_page(self) -> None:
        """
        Hide the currently visible window, if any.
        """
        if self.current_window:
            self.current_window.hide()

    @asyncSlot(str, int)
    async def __login_successful(self, name: str, user_id: int) -> None:
        """
        Callback invoked when a user logs in successfully.

        Initializes all available minigames for the authenticated user,
        dynamically constructing their models, views, and controllers.

        Args:
            name (str): The username of the logged-in user.
            user_id (int): The unique identifier of the user.

        Raises:
            Exception: If initialization of any minigame fails.
        """
        try:
            # --- FUT Game factory ---
            fut_storage = SQLiteCollectionStorage("./Assets/users.db")
            await fut_storage.initialize_connection()
            fut_api = FutApi("https://api.futdatabase.com/api/players/", "0f395e2f-2005-940c-ccb7-f95a2b4a4d0d")

            def fut_factory():
                fut_model = FUTModel(fut_storage, fut_api)
                fut_view = FUTMainView()
                return FUTController(fut_view, fut_model, name, user_id)

            self.hub_controller.add_game(
                fut_factory,
                "Fut Pack Opener",
                "Fifa based pack opener",
                "./Assets/pack_image.png"
            )

            # --- Risk Game factory ---
            async def risk_factory():
                risk_storage = SQLiteRiskGameStorage("./Assets/users.db")
                await risk_storage.initialize_connection()
                risk_model = RiskGameModel(risk_storage)
                await risk_model.init_state(user_id)
                risk_view = RiskGameView()
                return RiskGameController(risk_view, risk_model, name, user_id)

            self.hub_controller.add_game(
                risk_factory,
                "Football Risk Game",
                "Risk gambling game",
                "./Assets/gambling.jpg"
            )

            # --- Snake Game factory ---
            async def snake_factory():
                snake_storage = SQLiteSnakeGameStorage("./Assets/users.db")
                await snake_storage.initialize_connection()
                snake_model = SnakeGameModel(snake_storage)
                await snake_model.init_state(user_id)
                snake_view = SnakeGameView()
                return SnakeController(snake_view, snake_model, name, user_id)

            self.hub_controller.add_game(
                snake_factory,
                "Snake Game",
                "Basic Snake Game",
                "./Assets/snake_logo.jpg"
            )

            # --- Minesweeper factory ---
            def minesweeper_factory():
                ms_model = DummyModel()
                ms_view = MineSweeperView()
                return MineSweeperController(ms_view, ms_model, name, user_id)

            self.hub_controller.add_game(
                minesweeper_factory,
                "MineSweeper",
                "Classic minesweeper game",
                "./Assets/minesweeper_logo.jpg"
            )

            # --- Dribble King factory ---
            async def dribble_factory():
                dribble_storage = SQLiteDribbleKingStorage("./Assets/users.db")
                await dribble_storage.initialize_connection()
                dribble_model = DribbleKingModel(dribble_storage)
                await dribble_model.init_state(user_id)
                dribble_view = DribbleKingView(dribble_model)
                return DribbleKingController(dribble_view, dribble_model, name, user_id)

            self.hub_controller.add_game(
                dribble_factory,
                "Dribble King",
                "Dribble ball between cones",
                "./Assets/dribble.png"
            )

            # --- Reflex Game factory ---
            def reflex_factory():
                reflex_model = ReflexGameModel(800, 600)
                reflex_view = ReflexGameView(reflex_model)
                return ReflexGameController(reflex_model, reflex_view, name, user_id)

            self.hub_controller.add_game(
                reflex_factory,
                "ReflexGame",
                "Save falling balls",
                "./Assets/gloves.png"
            )

            self.hub_controller.set_user(name, user_id)

        except Exception as e:
            self.__show_error_message([str(e)])
            self.show_new_window(self.home_window)

    def __initialize_minigame(self) -> None:
        """
        Reinitialize minigame-related components.

        Used after cleanup to rebuild minigame modules from scratch.
        Creates new instances of authentication and hub components.
        """
        self.user_storage = SQLiteUserStorage("./Assets/users.db")
        self.auth_model: IAuthModel = AuthModel(self.user_storage)
        self.login_page: LoginPage = LoginPage()
        self.register_page: RegisterPage = RegisterPage()
        self.minigame_hub_view: MiniGameHubView = MiniGameHubView("", -1, [])
        self.auth_controller = AuthController(self.user_storage, self.auth_model, self.login_page, self.register_page)
        self.hub_controller = HubController(self.minigame_hub_view)

        self.__init_minigame_connections()

    def __init_minigame_connections(self) -> None:
        """
        Bind all signals and event connections for minigame-related controllers.

        Connects user authentication events, view transitions, and error handling
        between `AuthController` and `HubController`.
        """
        # Auth Controller signals
        self.auth_controller.login_successful.connect(lambda name, user_id: self.__login_successful(name, user_id))
        self.auth_controller.switch_to_view.connect(lambda widget: self.show_new_window(widget))
        self.auth_controller.error_occurred.connect(lambda errors: self.__show_error_message(errors))
        self.auth_controller.return_to_home.connect(lambda: self.__cleanup_minigame())
        self.auth_controller.registration_successful.connect(
            lambda information: self.__show_information_message(information))

        # HubController signals
        self.hub_controller.switch_to_view.connect(lambda widget: self.show_new_window(widget))
        self.hub_controller.return_to_home.connect(lambda: self.__cleanup_minigame())
        self.hub_controller.error_occurred.connect(lambda errors: self.__show_error_message(errors))
        self.hub_controller.information.connect(lambda information: self.__show_information_message(information))

    @asyncSlot()
    async def __cleanup_minigame(self) -> None:
        """
        Reset the minigame environment and return to the main home window.

        Behavior:
            - Closes all minigame-related windows and cleans up their resources.
            - Releases memory by deleting controller and view references.
            - Forces garbage collection.
            - Reinitializes the minigame subsystem for future sessions.
        """
        self.show_new_window(self.home_window)

        await self.auth_controller.cleanup()
        await self.hub_controller.cleanup()

        self.hub_controller.deleteLater()
        self.auth_controller.deleteLater()

        self.user_storage = None
        self.auth_model = None
        self.login_page = None
        self.register_page = None
        self.minigame_hub_view = None
        self.auth_controller = None
        self.hub_controller = None

        gc.collect()

        self.__initialize_minigame()

    @asyncSlot()
    async def __switch_to_prediction(self) -> None:
        """
        Navigate to the prediction module.

        Fetches available leagues asynchronously before displaying the
        prediction hub view.
        """
        success = await self.prediction_controller.fetch_league()
        if success:
            self.show_new_window(self.prediction_league_view)

    def __initialize_prediction(self) -> None:
        """
        Initialize the prediction module with predefined leagues.

        Adds all supported football leagues to the `PredictionModel`
        and binds related UI signals to the prediction controller.
        """

        self.prediction_model.add_league("PL")
        self.prediction_model.add_league("PD")
        self.prediction_model.add_league("FL1")
        self.prediction_model.add_league("BL1")
        self.prediction_model.add_league("SA")

        self.__init_prediction_connections()

    def __init_prediction_connections(self) -> None:
        """
        Establish all signal connections for the prediction controller.

        Connects return-to-home, navigation, and message events to
        their respective handlers.
        """
        self.prediction_controller.return_to_home.connect(lambda: self.show_new_window(self.home_window))
        self.prediction_controller.switch_to_view.connect(lambda widget: self.show_new_window(widget))
        self.prediction_controller.error_occurred.connect(lambda errors: self.__show_error_message(errors))
        self.prediction_controller.information.connect(lambda information: self.__show_information_message(information))

    def __switch_to_statistics(self) -> None:
        """
        Navigate to the statistics module.

        Displays the main statistics index view.
        """
        self.show_new_window(self.statistics_index_view)

    def __initialize_statistics(self) -> None:
        """
        Initialize the statistics module with supported leagues and
        establish signal connections to the controller.
        """

        self.statistics_model.add_league("PL", "PL")
        self.statistics_model.add_league("PD", "PD")
        self.statistics_model.add_league("FL1", "FL1")
        self.statistics_model.add_league("BL1", "BL1")
        self.statistics_model.add_league("SA", "SA")

        self.__init_statistics_connections()

    def __init_statistics_connections(self) -> None:
        """
        Establish all signal connections for the statistics controller.

        Handles home navigation, view switching, and message display events.
        """
        self.statistics_controller.return_to_home.connect(lambda: self.show_new_window(self.home_window))
        self.statistics_controller.switch_to_view.connect(lambda widget: self.show_new_window(widget))
        self.statistics_controller.error_occurred.connect(lambda errors: self.__show_error_message(errors))
        self.statistics_controller.information.connect(lambda information: self.__show_information_message(information))

    def __switch_to_training(self) -> None:
        """
        Navigate to the training module.

        Displays the training editor view and binds all related connections.
        """
        self.show_new_window(self.training_edit_view)
        self.__init_training_connections()

    def __init_training_connections(self) -> None:
        """
        Bind all signals and event connections for the training controller.

        Includes view switching, home navigation, and message handling.
        """
        self.training_controller.return_to_home.connect(lambda: self.show_new_window(self.home_window))
        self.training_controller.switch_to_view.connect(lambda widget: self.show_new_window(widget))
        self.training_controller.error_occurred.connect(lambda errors: self.__show_error_message(errors))
        self.training_controller.information.connect(lambda information: self.__show_information_message(information))

    @staticmethod
    def __show_error_message(errors) -> None:
        """
        Display an error message box.

        Args:
            errors (list[str] | str): A list or single string describing the error(s).
        """
        msg = ErrorMessageBox(errors)
        msg.exec()

    @staticmethod
    def __show_information_message(information) -> None:
        """
        Display an informational message box.

        Args:
            information (list[str] | str): Message(s) to display to the user.
        """
        msg = InfoMessageBox(information)
        msg.exec()

    async def __initialize_persistence(self) -> None:
        """
        Asynchronously initialize persistent storage connections.

        Ensures that SQLite databases and prediction storage layers are ready
        before user interaction begins.
        """
        await self.user_storage.initialize_connection()
        await self.prediction_storage.initialize_connection()
