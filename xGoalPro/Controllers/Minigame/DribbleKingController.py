from Controllers.Minigame.BaseGameController import BaseGameController
from Assets.utils import LANES
from qasync import asyncSlot


class DribbleKingController(BaseGameController):
    """
    Controller for the 'Dribble King' mini-game.

    Manages interactions between the Dribble King game model and its view,
    including player movement, leaderboard management, and game state updates.
    Handles asynchronous communication with the model and ensures smooth UI
    updates using Qt signals and slots.

    Inherits from:
        BaseGameController: Provides shared signals, model/view management,
        and cleanup routines for all mini-game controllers.

    Attributes:
        __is_closing (bool):
            Indicates whether the controller is in the process of shutting down,
            preventing updates or signal emissions during cleanup.
    """

    def __init__(self, view, model, user, user_id):
        """
        Initialize the Dribble King controller and connect signals.

        Args:
            view (DribbleKingView): The view responsible for rendering the game UI.
            model (DribbleKingModel): The model containing game logic and score handling.
            user (str): The username of the current player.
            user_id (int): The unique identifier of the current player.
        """
        super().__init__(view, model, user, user_id)
        self.__is_closing = False
        self.__init_connection()

    async def cleanup(self) -> None:
        """
        Clean up resources and safely disconnect all signals.

        This method prevents any pending async updates or signal emissions,
        disconnects model and view signals, and ensures the model’s storage
        and resources are closed gracefully.
        """
        self.__is_closing = True

        # Disconnect all signals
        self.model.updated.disconnect()

        self.view.move_left.disconnect()
        self.view.move_right.disconnect()
        self.view.return_to_hub.disconnect()
        self.view.restart_clicked.disconnect()
        self.view.leaderboard_btn_clicked.disconnect()
        self.view.start_game.disconnect()

        # Close storage safely
        try:
            await self.model.cleanup()
        except Exception as e:
            print("[DribbleKingController] storage close error:", e)

    def __init_connection(self) -> None:
        """
        Initialize all signal-slot connections between the view and model.

        Connects user input (movement, restart, leaderboard requests) to
        corresponding controller logic, and subscribes to the model’s
        update events for live UI updates.
        """
        self.view.move_left.connect(lambda: self.__move_left())
        self.view.move_right.connect(lambda: self.__move_right())
        self.view.return_to_hub.connect(lambda: self.__return_to_hub_handle())
        self.view.restart_clicked.connect(lambda: self.model.start())
        self.view.leaderboard_btn_clicked.connect(lambda: self.__on_show_leaderboard())
        self.view.start_game.connect(lambda: self.model.start())

        self.model.updated.connect(lambda: self.__update_state())

    def __move_left(self) -> None:
        """
        Move the player character one lane to the left.

        Ensures that movement stays within the defined lane boundaries.
        """
        self.model.lane = max(0, self.model.lane-1)

    def __move_right(self) -> None:
        """
        Move the player character one lane to the right.

        Ensures that movement does not exceed the maximum number of lanes.
        """
        self.model.lane = min(LANES-1, self.model.lane+1)

    def __return_to_hub_handle(self) -> None:
        """
        Handle the 'return to hub' action by emitting the corresponding signal.
        """
        self.return_to_hub.emit()

    @asyncSlot()
    async def __update_state(self) -> None:
        """
        Asynchronously update the game state and UI.

        Called whenever the model signals an update. Handles game rendering,
        checks for game-over conditions, and triggers score saving.
        """
        if self.__is_closing or not self.model or not self.view:
            return

        try:
            self.view.index_view.update()
            if self.model.game_over:
                await self.model.save_score(self.user_id)
        except RuntimeError:
            # View deleted or controller gone
            return
        except Exception as e:
            # Only emit if still alive
            if not self.__is_closing:
                try:
                    self.error_occurred.emit([f"Update state error: {e}"])
                except RuntimeError:
                    pass

    @asyncSlot()
    async def __on_show_leaderboard(self) -> None:
        """
        Asynchronously fetch and display the game leaderboard.

        Retrieves the top 10 player scores from storage and updates
        the leaderboard view. Emits an error signal if the operation fails.
        """
        try:
            leaderboard = await self.model.get_scores(limit=10)
            formatted = [(i + 1, row["username"], row["high_score"]) for i, row in enumerate(leaderboard)]
            self.view.refresh_leaderboard(formatted)
        except Exception as e:
            self.error_occurred.emit([f"Leaderboard error: {e}"])
            self.view.show_index()
            self.switch_to_view(self.view)
