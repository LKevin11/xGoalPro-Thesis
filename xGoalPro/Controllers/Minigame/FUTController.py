import asyncio

from qasync import asyncSlot

from Controllers.Minigame.BaseGameController import BaseGameController

from View.Components.LoadingWidget import LoadingWidget

from PyQt5.QtWidgets import QApplication

from ResourcePath import resource_path


class FUTController(BaseGameController):
    """
    Controller for the 'FUT Pack Opener' mini-game.

    Coordinates interactions between the FUT game model and its associated view.
    Handles asynchronous operations such as pack opening and card collection browsing,
    while maintaining responsive UI updates via Qt signal-slot connections.

    Inherits from:
        BaseGameController: Provides base attributes, signals, and cleanup logic for all mini-game controllers.
    """

    def __init__(self, view, model, user, user_id):
        """
        Initialize the FUTController and establish all required signal connections.

        Args:
            view (FUTView): The user interface for the FUT pack opening game.
            model (FUTModel): The data and logic handler for FUT pack operations.
            user (str): The username of the current player.
            user_id (int): The unique identifier of the current player.
        """
        super().__init__(view, model, user, user_id)

        self.init_connections()

    def init_connections(self):
        """
        Initialize all Qt signal-slot connections between the view and controller.

        Connects user interface actions (such as pack opening and collection navigation)
        to their respective controller handlers.
        """
        self.view.return_to_hub.connect(lambda: self.return_to_hub.emit())
        self.view.open_btn_clicked.connect(self.open_pack)
        self.view.collection_btn_clicked.connect(self.get_collection)
        self.view.prev_btn_clicked.connect(self.get_collection)
        self.view.next_btn_clicked.connect(self.get_collection)

    @asyncSlot()
    async def open_pack(self):
        """
        Asynchronously handle the pack opening process.

        Displays a loading animation, requests the model to open a new pack,
        and updates the view with the resulting card image. The view automatically
        disables the open button during processing and reenables it after a short delay.

        Emits:
            - error_occurred (list): If the model fails to open the pack.
            - switch_to_view (QWidget): When switching between loading and main views.
        """
        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Opening pack ...")
        self.switch_to_view.emit(loading)

        QApplication.processEvents()

        success, message = await self.model.open_pack(self.user, self.user_id)

        if success:
            self.view.set_pack_image_from_bytes(message[0])
            self.view.index_view.disable_open_btn()
            self.switch_to_view.emit(self.view)
            loading.deleteLater()

            await asyncio.sleep(5)

            self.view.set_pack_image(resource_path("./Assets/pack_image.png"))
            self.view.index_view.enable_open_btn()
        else:
            self.error_occurred.emit(message)
            self.switch_to_view.emit(self.view)

    @asyncSlot(int)
    async def get_collection(self, direction: int):
        """
        Asynchronously fetch and display the player's FUT card collection.

        Args:
            direction (int): The navigation direction.
                - 0 typically represents the first fetch or refresh.
                - -1 navigates to the previous page.
                - +1 navigates to the next page.

        Displays a loading animation, retrieves cards from the model, and
        updates navigation buttons based on availability of additional pages.

        Emits:
            - error_occurred (list): If the collection fetch fails.
            - switch_to_view (QWidget): When switching between loading and collection views.
        """

        loading = LoadingWidget(resource_path("./Assets/loading.gif"), "Fetching collection ...")
        self.switch_to_view.emit(loading)

        QApplication.processEvents()

        success, message = await self.model.fetching_cards(self.user, direction)

        if success:
            self.view.refresh_collection_view(message)

            # Enable/disable navigation buttons
            if self.model.can_go_prev():
                self.view.collection_view.enable_prev_btn()
            else:
                self.view.collection_view.disable_prev_btn()

            if self.model.can_go_next():
                self.view.collection_view.enable_next_btn()
            else:
                self.view.collection_view.disable_next_btn()

            self.switch_to_view.emit(self.view)
            loading.deleteLater()

        else:
            self.error_occurred.emit(message)
            self.view.show_index()
            self.switch_to_view.emit(self.view)
