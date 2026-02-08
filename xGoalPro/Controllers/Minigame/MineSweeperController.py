import subprocess
from Controllers.Minigame.BaseGameController import BaseGameController
from PyQt5.QtCore import QTimer

from ResourcePath import resource_path


class MineSweeperController(BaseGameController):
    """
    Controller for the MineSweeper mini-game.

    This controller launches and monitors an external MineSweeper executable
    (`MineSweeper.exe`) as part of the mini-game suite. It integrates process
    lifecycle management into the PyQt5 event loop using `QTimer` to periodically
    check if the external process is still running.

    Inherits:
        BaseGameController: Provides base game controller functionality, including
        signal handling and resource cleanup.
    """

    def __init__(self, view, model, user, user_id):
        """
        Initialize the MineSweeper controller.

        Args:
            view (QWidget): The view associated with the MineSweeper game.
            model (GameModel): The model handling persistence and data logic.
            user (str): The username of the current player.
            user_id (int): Unique identifier of the current user.
        """
        super().__init__(view, model, user, user_id)

        self.__wf_process = None  # consistent name
        self.__init_connections()

        # Timer to check if the external process is still running
        self.__timer: QTimer = QTimer(self)
        self.__timer.timeout.connect(self.__check_wf)
        self.__timer.start(1000)  # keep running, safe to poll

    def __init_connections(self) -> None:
        """
        Initialize all signal-slot connections for the view.

        Connects UI signals (start, back, close) to the appropriate controller methods.
        """
        # Connect view signals to controller slots
        self.view.back_to_hub.connect(lambda: self.return_to_hub.emit())
        self.view.start_game.connect(self.__start_game)
        self.view.about_to_close.connect(self.__close_process)

    def __start_game(self) -> None:
        """
        Launch the external MineSweeper executable as a subprocess.

        This method ensures that any previously running process is terminated before
        starting a new one. If successful, the view disables its UI buttons until
        the process completes.

        Emits:
            error_occurred (list): If launching the game fails.
        """
        try:
            # Close old process if it exists
            if self.__wf_process is not None:
                self.__close_process()

            self.__wf_process = subprocess.Popen(
                [resource_path(r"./Assets/MineSweeperWF/MineSweeper.exe")],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.view.disable_buttons()

        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.view.enable_buttons()
            self.switch_to_view.emit(self.view)

    def __check_wf(self) -> None:
        """
        Periodically check the status of the MineSweeper process.

        This method is called by a `QTimer` every second to verify if the
        external game process has exited. If the process has finished, the view
        is re-enabled to allow another game launch.
        """
        if self.__wf_process is None:
            return

        try:
            # poll() returns None while running, exit code when finished
            if self.__wf_process.poll() is not None:
                self.view.enable_buttons()
                self.__wf_process = None  # reset for next run

        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.view.enable_buttons()
            self.switch_to_view.emit(self.view)

    def __close_process(self) -> None:
        """
        Safely terminate the external MineSweeper process if it is running.

        Called when the view is about to close or a new process is launched.
        Ensures that the process exits cleanly to prevent orphaned background tasks.

        Emits:
            error_occurred (list): If termination fails.
        """
        try:
            if self.__wf_process is not None and self.__wf_process.poll() is None:
                self.__wf_process.terminate()
                self.__wf_process.wait(timeout=1)  # safely wait for termination
        except Exception as e:
            self.error_occurred.emit([str(e)])
        finally:
            self.view.enable_buttons()
            self.__wf_process = None
