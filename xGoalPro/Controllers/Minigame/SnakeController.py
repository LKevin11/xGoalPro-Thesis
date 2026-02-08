import asyncio
import subprocess
from Controllers.Minigame.BaseGameController import BaseGameController
from PyQt5.QtCore import QTimer
from qasync import asyncSlot
from ResourcePath import resource_path


class SnakeController(BaseGameController):
    """
    Controller for the Snake mini-game (WPF version).

    This controller manages the interaction between the PyQt5 interface and
    the external WPF Snake executable. It handles game process management,
    leaderboard display, and safe cleanup when returning to the hub.

    Inherits:
        BaseGameController: Provides a unified interface for all mini-game controllers.
    """

    def __init__(self, view, model, user, user_id):
        """
        Initialize the SnakeController.

        Args:
            view: The PyQt5 view responsible for displaying the game UI.
            model: The game model handling score persistence and leaderboard access.
            user (str): The username of the current player.
            user_id (int): The player’s unique identifier.
        """
        super().__init__(view, model, user, user_id)

        self.__wpf_process = None

        # wire up view signals
        self.__init_connections()

        # Timer to periodically check WPF process
        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__check_wpf)
        self.__timer.start(1000)  # keep running; __check_wpf exits if no process

    def __init_connections(self) -> None:
        """
        Connect view signals to controller event handlers.

        Sets up UI-to-controller communication for game start, navigation,
        leaderboard access, and safe cleanup when closing the window.
        """
        # connect view signals to controller signals / handlers
        self.view.back_to_hub.connect(lambda: self.return_to_hub.emit())
        self.view.start_game.connect(lambda: self.__start_game())
        self.view.about_to_close.connect(lambda: self.__close_process())
        self.view.leaderboard_btn_clicked.connect(lambda: self.__show_leaderboard())

    def __start_game(self) -> None:
        """
        Launch the external WPF Snake game.

        Starts the executable and disables the interface buttons while the game
        is running. Any previously running instance is safely terminated first.
        """
        try:
            # if a previous process exists, close it first
            if self.__wpf_process is not None:
                self.__close_process()

            # start WPF game
            self.__wpf_process = subprocess.Popen(
                [resource_path(r"./Assets/SnakeGameWPF/Snake.WPF.exe")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # disable buttons while game is running
            self.view.index_view.disable_buttons()

        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.view.index_view.enable_buttons()
            self.switch_to_view.emit(self.view)

    def __check_wpf(self) -> None:
        """
        Monitor the running WPF process and handle completion.

        - Detects when the external process exits.
        - Attempts to parse the output for a final score.
        - Updates and saves the score asynchronously if valid.
        - Re-enables the UI once the process has finished.
        """
        if self.__wpf_process is None:
            return  # nothing to check

        if self.__wpf_process.poll() is not None:  # process finished
            try:
                try:
                    output, _ = self.__wpf_process.communicate(timeout=0.1)
                except subprocess.TimeoutExpired:
                    output = None

                if output:
                    try:
                        score = int(output.strip())
                        self.model.score = score
                        if score > self.model.high_score:
                            self.model.high_score = score
                        asyncio.create_task(self.model.save_score(self.user_id))
                    except ValueError:
                        pass

            finally:
                # reset GUI and process state
                self.view.index_view.enable_buttons()
                self.__wpf_process = None

    @asyncSlot()
    async def __show_leaderboard(self) -> None:
        """
        Fetch and display the leaderboard asynchronously.

        Retrieves the top scores from persistent storage and refreshes
        the leaderboard view. Falls back to the index screen on error.
        """
        try:
            leaderboard = await self.model.get_leaderboard(limit=10)
            self.view.refresh_leaderboard(leaderboard)
            self.view.show_leaderboard()
        except Exception as e:
            self.error_occurred.emit([f"Leaderboard error: {e}"])
            self.view.show_index()

    def __close_process(self) -> None:
        """
        Safely terminate the WPF Snake process.

        Called when:
            - The view is closing.
            - A new game starts and an old process is still running.
            - Cleanup is triggered from the hub controller.
        """
        try:
            if self.__wpf_process is not None and self.__wpf_process.poll() is None:
                self.__wpf_process.terminate()
                self.__wpf_process.wait(timeout=1)
        except Exception as e:
            self.error_occurred.emit([str(e)])
        finally:
            # ensure buttons are enabled and process is cleared
            self.view.index_view.enable_buttons()
            self.__wpf_process = None
