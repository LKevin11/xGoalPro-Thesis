from PyQt5.QtCore import Qt
from Controllers.Minigame.BaseGameController import BaseGameController


class ReflexGameController(BaseGameController):
    """
    Controller for the Reflex mini-game.

    This class handles all user input (keyboard and mouse) and updates the
    game model accordingly. It connects the view’s signals to the model’s
    movement and state logic, ensuring responsive real-time paddle control.

    Inherits:
        BaseGameController: Provides core controller functionality for minigames.
    """
    def __init__(self, model, view, user, user_id):
        """
        Initialize the Reflex game controller.

        Args:
            model: The game model handling state updates and logic.
            view: The associated view for rendering the game.
            user (str): The username of the current player.
            user_id (int): The player’s unique identifier.
        """
        super().__init__(view, model, user, user_id)
        self.model = model
        self.view = view

        self.__left_pressed = False
        self.__right_pressed = False

        # Init connections
        view.move_paddle_signal.connect(self.model.move_paddle_to)
        view.mouse_press_signal.connect(self.__on_mouse_press)
        view.key_press_signal.connect(self.__on_key_press)
        view.key_release_signal.connect(self.__on_key_release)
        view.back_btn_pressed.connect(lambda: self.return_to_hub.emit())
        self.model.timer.timeout.connect(self.__keyboard_tick)
        self.model.game_over.connect(self.__on_game_over)
        self.model.start()

    def __on_key_press(self, key) -> None:
        """
        Handle key press events.

        Controls:
            - Left Arrow: Move paddle left.
            - Right Arrow: Move paddle right.
            - Space: Pause/resume the game.
            - R: Restart the game.
        """
        if key == Qt.Key_Left:
            self.__left_pressed = True
        elif key == Qt.Key_Right:
            self.__right_pressed = True
        elif key == Qt.Key_Space:
            self.model.toggle_pause()
        elif key == Qt.Key_R:
            self.model.reset()

    def __on_key_release(self, key) -> None:
        """
        Handle key release events.

        Updates the internal key state tracking so continuous
        movement stops when the player releases a key.
        """
        if key == Qt.Key_Left:
            self.__left_pressed = False
        elif key == Qt.Key_Right:
            self.__right_pressed = False

    def __on_mouse_press(self) -> None:
        """
        Handle mouse click events.

        Behavior:
            - If instructions are visible, hide them and start the game.
            - If the game is over, reset and restart.
            - Otherwise, toggle pause/resume during gameplay.
        """
        if self.model.show_instructions:
            # Just hide the instructions and start the timer
            self.model.show_instructions = False
            self.model.start()
        elif self.model.is_game_over:
            # Restart game after game over
            self.model.reset()
            self.model.show_instructions = False
        else:
            # Toggle pause during game
            self.model.toggle_pause()

    def __keyboard_tick(self) -> None:
        """
        Update paddle position based on held keyboard input.

        Called by the model’s timer at each tick. Calculates delta movement
        (`dx`) using the paddle’s speed and the timer’s interval, and moves
        the paddle accordingly.
        """
        if self.model.paused or self.model.is_game_over or self.model.show_instructions:
            return
        dt = self.model.timer.interval() / 1000.0
        dx = 0
        if self.__left_pressed:
            dx -= self.model.paddle.speed * dt
        if self.__right_pressed:
            dx += self.model.paddle.speed * dt
        if dx != 0:
            self.model.move_paddle_by(dx)

    def __on_game_over(self) -> None:
        """
        Handle the game-over event.

        Stops the model timer to prevent further updates until reset.
        """
        self.model.stop()
