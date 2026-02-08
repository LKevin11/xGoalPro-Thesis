from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget
from Model.GameModel import GameModel


class BaseGameController(QObject):
    """
    Abstract base controller for game modules.

    Provides a shared interface and common signal structure for all game controllers
    in the application. Handles the linkage between a game's view, model, and user context,
    and defines cleanup routines for releasing UI and model resources.

    Signals:
        return_to_hub (pyqtSignal):
            Emitted to navigate back to the game hub or main menu.
        switch_to_view (pyqtSignal[QWidget]):
            Emitted to request switching the currently displayed game view.
        error_occurred (pyqtSignal[list]):
            Emitted when an error occurs, passing a list of error messages.
        information (pyqtSignal[list]):
            Emitted to display informational messages to the user.

    Attributes:
        view (QWidget): 
            The current game view instance managed by the controller.
        model (GameModel): 
            The game model containing logic, state, and data for the game.
        user (str): 
            The username of the currently logged-in player.
        user_id (int): 
            The unique identifier of the player.
    """

    return_to_hub: pyqtSignal = pyqtSignal()
    switch_to_view: pyqtSignal(QWidget) = pyqtSignal(QWidget)
    error_occurred: pyqtSignal(list) = pyqtSignal(list)
    information: pyqtSignal(list) = pyqtSignal(list)

    def __init__(self, view: QWidget, model: GameModel, user: str, user_id: int):
        """
        Initialize the base game controller.

        Args:
            view (QWidget): The QWidget representing the game's visual interface.
            model (GameModel): The model instance that controls game logic and state.
            user (str): The username of the player currently playing the game.
            user_id (int): The unique ID of the player.
        """
        super().__init__()

        self.view: QWidget = view
        self.model: GameModel = model
        self.user: str = user
        self.user_id: int = user_id

    async def cleanup(self) -> None:
        """
        Clean up the game controller and release resources.

        Deletes the associated game view, closes and cleans up the game model, 
        and removes model references to allow proper garbage collection.
        """
        self.view.deleteLater()
        await self.model.cleanup()
        self.model = None
