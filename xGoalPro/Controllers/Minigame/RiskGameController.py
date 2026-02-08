from qasync import asyncSlot

from Controllers.Minigame.BaseGameController import BaseGameController


class RiskGameController(BaseGameController):
    """
    Controller for the Football Risk mini-game.

    This controller coordinates between the view and model layers, handling
    asynchronous gameplay logic such as advancing, banking points, resetting
    progress, and displaying the leaderboard.

    Inherits:
        BaseGameController: Provides common signals and lifecycle management
        for all mini-game controllers.
    """

    def __init__(self, view, model, user, user_id):
        """
        Initialize the Soccer Risk controller.

        Args:
            view: The PyQt5 view instance that renders the game interface.
            model: The game model handling score logic, persistence, and state.
            user (str): Username of the active player.
            user_id (int): Unique identifier for the current player.
        """
        super().__init__(view, model, user, user_id)

        self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)
        self.view.append_log('Welcome to Football Risk — Advance carefully!')
        self.__init_connections()

    def __init_connections(self) -> None:
        """
        Connect all view signals to their respective controller handlers.

        This includes gameplay actions (advance, hold, reset, new attack),
        navigation (return to hub), and leaderboard display.
        """
        self.view.advance_btn_clicked.connect(self.__on_advance)
        self.view.hold_btn_clicked.connect(self.__on_hold)
        self.view.new_btn_clicked.connect(self.__on_new_attack)
        self.view.reset_btn_clicked.connect(self.__on_reset)
        self.view.return_to_hub.connect(lambda: self.return_to_hub.emit())
        self.view.leaderboard_btn_clicked.connect(self.__on_show_leaderboard)

    @asyncSlot()
    async def __on_advance(self) -> None:
        """
        Handle the 'Advance' button action.

        - Starts a new attack if one isn't in progress.
        - Calls the model to advance the player's position asynchronously.
        - Updates the score display and emits notifications depending on
          the outcome ('tackled' or 'banked').
        """
        if not self.model.in_attack:
            self.model.reset_attack()
            self.view.append_log('Starting a new attack...')

        try:
            result, msg = await self.model.advance(self.user_id)

            self.view.append_log(msg)

            self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)

            if result == 'tackled':
                self.information.emit(['Tackled!'])
                # After being tackled, start a new attack automatically
                self.model.reset_attack()
                self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)
            elif result == 'banked':
                self.information.emit(['Scored!'])
                self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)

        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.switch_to_view(self.view)

    @asyncSlot()
    async def __on_hold(self) -> None:
        """
        Handle the 'Hold' button action.

        - Banks the current attack score into the player’s long-term bank.
        - Starts a new attack automatically after banking.
        - Validates that there’s something to bank before proceeding.
        """
        try:
            if self.model.current == 0:
                self.view.append_log('Nothing to bank — try advancing first.')
                return
            banked = await self.model.hold(self.user_id)
            self.view.append_log(f'You banked {banked} points into long-term score. A new attack begins!')
            self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.switch_to_view.emit(self.view)

    @asyncSlot()
    async def __on_new_attack(self) -> None:
        """
        Start a new attack.

        Resets the model’s attack state and updates the UI to reflect
        a fresh start.
        """
        try:
            self.model.reset_attack()
            self.view.append_log('New attack started (position and current reset).')
            self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.switch_to_view(self.view)

    @asyncSlot()
    async def __on_reset(self) -> None:
        """
        Reset the player's entire game progress.

        Clears the banked score, current score, and high score both in
        the model and the view.
        """
        try:
            await self.model.reset_progress(self.user_id)
            self.view.append_log('Progress reset. Bank and high score set to 0.')
            self.view.update_scores(self.model.bank, self.model.current, self.model.position, self.model.high_score)
        except Exception as e:
            self.error_occurred.emit([str(e)])
            self.switch_to_view.emit(self.view)

    @asyncSlot()
    async def __on_show_leaderboard(self) -> None:
        """
        Fetch and display the top leaderboard asynchronously.

        Retrieves high scores from the model, formats the leaderboard data,
        and displays it in the view. On error, emits a message and falls
        back to the index screen.
        """
        try:
            leaderboard = await self.model.get_scores(limit=10)
            formatted = [(i + 1, row["username"], row["high_score"]) for i, row in enumerate(leaderboard)]
            self.view.refresh_leaderboard(formatted)
            self.view.show_leaderboard()
        except Exception as e:
            self.error_occurred.emit([f"Leaderboard error: {e}"])
            self.view.show_index()
            self.switch_to_view(self.view)
