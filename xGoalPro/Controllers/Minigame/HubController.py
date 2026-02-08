from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget
from qasync import asyncSlot
import asyncio

from GameProperties import GameProperties

from View.Minigame.MinigameHub import MiniGameHubView


class HubController(QObject):
    """
    Central controller for the MiniGame Hub.

    The `HubController` acts as the entry point for all mini-games. It manages
    user session data, dynamically loads game controllers via factories,
    handles asynchronous cleanup, and switches between the hub and game views.

    Signals:
        return_to_home (pyqtSignal): Emitted when returning to the application home screen.
        switch_to_view (pyqtSignal(QWidget)): Emitted when switching between hub and game views.
        error_occurred (pyqtSignal(list)): Emitted when an error occurs.
        information (pyqtSignal(list)): Emitted for general information or notifications.
    """

    return_to_home: pyqtSignal = pyqtSignal()
    switch_to_view: pyqtSignal(QWidget) = pyqtSignal(QWidget)
    error_occurred: pyqtSignal(list) = pyqtSignal(list)
    information: pyqtSignal(list) = pyqtSignal(list)

    def __init__(self, view):
        """
        Initialize the HubController with its associated view.

        Args:
            view (MiniGameHubView): The main UI view displaying available mini-games.
        """
        super().__init__()

        self.__user: str = ""
        self.__id: int = -1
        self.games: list[GameProperties] = []

        # View
        self.view: MiniGameHubView = view
        self.view.back_to_home.connect(lambda: self.return_to_home.emit())
        self.view.show_game.connect(lambda idx: self.__show_game(idx))

    def add_game(self, factory, name, description, image) -> None:
        """
        Add a new mini-game to the hub.

        Args:
            factory (Callable): A factory function or coroutine returning a game controller.
            name (str): The name of the game.
            description (str): A short description of the game.
            image (str): Path to the game's preview image.
        """
        game = GameProperties(None, name, description, image, factory)
        self.games.append(game)

    def remove_game(self, idx) -> None:
        """
        Remove a mini-game from the hub by index.

        Args:
            idx (int): The index of the game to remove.

        Emits:
            error_occurred (list): If the index is invalid.
        """
        if 0 <= idx < len(self.games):
            game = self.games.pop(idx)
            game.controller.return_to_hub.disconnect()
            self.refresh_view()
        else:
            self.error_occurred.emit(["Invalid game index"])

    def set_user(self, user, user_id) -> None:
        """
        Set the current user and refresh the hub view.

        Args:
            user (str): Username of the current player.
            user_id (int): Unique user identifier.
        """
        self.__user = user
        self.__id = user_id
        self.refresh_view()

    async def cleanup(self) -> None:
        """
        Clean up all mini-game controllers and the hub view.

        Iterates through all games, ensuring their controllers (if active)
        are cleaned up asynchronously and their resources released.
        """
        if self.games:
            for game in self.games:
                try:
                    # ensure controller exists
                    if game.controller is None and game.factory is not None:
                        if asyncio.iscoroutinefunction(game.factory):
                            controller = await game.factory()
                        else:
                            controller = game.factory()
                        game.controller = controller

                    # cleanup
                    if game.controller:
                        await game.controller.cleanup()
                        game.controller.deleteLater()
                        game.controller = None
                except Exception as e:
                    print(f"[Hub cleanup] Error cleaning {game.name}: {e}")
            self.games.clear()

        if self.view:
            self.view.deleteLater()
            self.view = None

    def refresh_view(self) -> None:
        """
        Refresh the hub view with the latest user and game data.

        Updates the hub interface to display the current user's information
        and all available games.
        """"""Update the view with current data"""
        self.view.update_content(self.__user, self.__id, self.games)
        self.switch_to_view.emit(self.view)

    @asyncSlot(int)
    async def __show_game(self, idx) -> None:
        """
        Handle game selection and transition to the selected game's view.

        Lazily initializes the game controller using its factory (sync or async),
        connects controller signals to the hub, and switches to the game view.

        Args:
            idx (int): Index of the selected game.

        Emits:
            error_occurred (list): If an invalid game index is provided.
        """
        if 0 <= idx < len(self.games):
            game = self.games[idx]

            # Lazy initialize only once
            if game.controller is None:
                factory = game.factory
                if asyncio.iscoroutinefunction(factory):
                    controller = await factory()  # await async factory
                else:
                    controller = factory()  # call sync factory

                game.controller = controller

                # connect signals
                controller.return_to_hub.connect(lambda: self.__on_return_to_hub(idx))
                controller.error_occurred.connect(lambda errors: self.error_occurred.emit(errors))
                controller.switch_to_view.connect(lambda widget: self.switch_to_view.emit(widget))
                controller.information.connect(lambda info: self.information.emit(info))

            self.switch_to_view.emit(game.controller.view)
        else:
            self.error_occurred.emit(["Invalid game selection"])

    def __on_return_to_hub(self, idx: int) -> None:
        """
        Handle cleanup and transition when returning from a game to the hub.

        Args:
            idx (int): Index of the game being closed.
        """
        game = self.games[idx]
        if game.controller:
            try:
                asyncio.create_task(game.controller.cleanup())
            except Exception:
                pass
            game.controller.deleteLater()
            game.controller = None
        self.switch_to_view.emit(self.view)
