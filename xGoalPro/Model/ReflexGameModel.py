import math
import random
from typing import List, Optional

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QColor

from Model.GameModel import GameModel


class Ball:
    """Represents a ball in the Reflex game.

    Attributes:
        x (float): X-coordinate of the ball.
        y (float): Y-coordinate of the ball.
        vx (float): X-axis velocity of the ball.
        vy (float): Y-axis velocity of the ball.
        radius (float): Radius of the ball.
        color (QColor): Ball color.
        hits (int): Number of times the ball has hit the paddle.
    """
    def __init__(self, x, y, vx, vy, radius=12.0, color=None):
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.radius: float = radius
        self.color: QColor = color or QColor(220, 60, 60)
        self.hits: int = 0


class Paddle:
    """Represents the paddle in the Reflex game.

    Attributes:
        x (float): X-coordinate of the paddle's center.
        y (float): Y-coordinate of the paddle's center.
        width (float): Paddle width.
        height (float): Paddle height.
        speed (float): Movement speed in pixels/second.
        color (QColor): Paddle color.
    """
    def __init__(self, x, y):
        self.x: float = x
        self.y: float = y
        self.width: float = 120.0
        self.height: float = 14.0
        self.speed: float = 800.0
        self.color: QColor = QColor(40, 120, 220)


class ReflexGameModel(GameModel):
    """Model for a Reflex-style paddle game.

    Handles ball physics, paddle movement, collision detection, scoring, and game state.
    Uses a QTimer for game loop updates and PyQt signals for UI updates.

    Signals:
        updated: Emitted on each game update to trigger UI refresh.
        game_over: Emitted when player loses all lives.

    Attributes:
        score (int): Current score.
        lives (int): Remaining lives.
        paused (bool): Whether the game is paused.
        is_game_over (bool): Whether the game has ended.
        balls (List[Ball]): List of balls in play.
        paddle (Paddle): The player’s paddle.
        show_instructions (bool): Whether instructions overlay is shown.
        width (int): Game field width in pixels.
        height (int): Game field height in pixels.
        timer (QTimer): Timer driving the game loop.
    """
    updated = pyqtSignal()
    game_over = pyqtSignal()

    def __init__(self, width=800, height=600):
        super().__init__()

        self.__gravity: float = 0.0
        self.__restitution: float = 0.0
        self.__spawn_interval: int = 1200
        self.__accum_spawn: int = 0

        self.score: int = 0
        self.lives: int = 3
        self.paused: bool = False
        self.is_game_over: bool = False
        self.balls: List[Ball] = []
        self.paddle: Optional[Paddle] = None
        self.show_instructions: bool = True
        self.width: int = width
        self.height: int = height
        self.timer: QTimer = QTimer()

        self.timer.setInterval(16)
        self.timer.timeout.connect(self.__tick)

        self.reset()

    def reset(self) -> None:
        """Reset the game to its initial state, spawning the first ball."""
        self.balls: List[Ball] = []
        self.paddle = Paddle(self.width / 2.0, self.height - 40)
        self.__gravity = 1400.0
        self.__restitution = 0.85
        self.__spawn_interval = 1200
        self.__accum_spawn = 0
        self.score = 0
        self.lives = 3
        self.paused = False
        self.is_game_over = False
        self.__spawn_ball(initial=True)
        self.updated.emit()
        if not self.timer.isActive():
            self.start()

    def start(self) -> None:
        """Start the game timer to begin the game loop."""
        self.timer.start()

    def stop(self) -> None:
        """Stop the game timer, pausing updates."""
        self.timer.stop()

    def toggle_pause(self):
        """Toggle the pause state if the game is running and instructions are hidden."""
        if not self.is_game_over and not self.show_instructions:
            self.paused = not self.paused
            self.updated.emit()

    def move_paddle_to(self, x_pos: float) -> None:
        """Move the paddle horizontally to a specific x-coordinate.

        Args:
            x_pos (float): Target x-coordinate for the paddle's center.
        """
        half = self.paddle.width / 2.0
        self.paddle.x = max(half, min(self.width - half, x_pos))
        self.updated.emit()

    def move_paddle_by(self, dx: float) -> None:
        """Move the paddle horizontally by a delta amount.

        Args:
            dx (float): Number of pixels to move the paddle by.
        """
        self.move_paddle_to(self.paddle.x + dx)

    async def cleanup(self) -> None:
        """Clean up resources, stopping the timer."""
        self.timer.deleteLater()

    def __tick(self) -> None:
        """Private slot called by the QTimer to update the game state each frame."""
        if not self.paused and not self.is_game_over and not self.show_instructions:
            self.__update(self.timer.interval())

    def __spawn_ball(self, initial=False) -> None:
        """Spawn a new ball with randomized position, velocity, and color.

        Args:
            initial (bool): Whether this is the initial ball at game start.
        """
        r = random.uniform(10, 16)
        x = random.uniform(80, self.width - 80)
        y = random.uniform(40, 120) if initial else 40
        vx = random.uniform(-160, 160)
        vy = random.uniform(0, 40)
        color = QColor(random.randint(180, 255), random.randint(50, 200), random.randint(50, 200))
        self.balls.append(Ball(x, y, vx, vy, r, color))

    def __update(self, dt_ms: float) -> None:
        """Update game physics, ball positions, collisions, and scoring.

        Args:
            dt_ms (float): Time elapsed since last tick in milliseconds.
        """
        dt = dt_ms / 1000.0
        self.__accum_spawn += dt_ms
        if self.__accum_spawn >= self.__spawn_interval:
            self.__spawn_ball()
            self.__accum_spawn = 0
            self.__spawn_interval = max(400, self.__spawn_interval - 20)

        for b in list(self.balls):
            b.vy += self.__gravity * dt
            b.x += b.vx * dt
            b.y += b.vy * dt
            if b.x - b.radius < 0:
                b.x = b.radius
                b.vx = -b.vx * self.__restitution
            if b.x + b.radius > self.width:
                b.x = self.width - b.radius
                b.vx = -b.vx * self.__restitution
            if b.y - b.radius < 0:
                b.y = b.radius
                b.vy = -b.vy * self.__restitution
            if b.y - b.radius > self.height:
                self.balls.remove(b)
                self.lives -= 1
                if self.lives <= 0:
                    self.is_game_over = True
                    self.game_over.emit()
                continue
            if self.__ball_hits_paddle(b):
                b.hits += 1
                if b.hits >= 3:
                    self.score += 1
                    self.balls.remove(b)
                    continue
                overlap = (self.paddle.y - (b.y + b.radius))
                b.y += overlap
                self.score += 1
                rel = ((b.x - self.paddle.x) / (self.paddle.width / 2.0))
                rel = max(-1.0, min(1.0, rel))
                speed = math.hypot(b.vx, b.vy) * 0.95 + 120
                angle = (rel * 0.6) + (-math.pi / 2)
                b.vx = math.cos(angle) * speed
                b.vy = -abs(math.sin(angle) * speed)
                b.vx += random.uniform(-40, 40)
        self.updated.emit()

    def __ball_hits_paddle(self, b) -> bool:
        """Check whether a given ball collides with the paddle.

        Args:
            b (Ball): The ball to check collision for.

        Returns:
            bool: True if the ball collides with the paddle, False otherwise.
        """

        px1 = self.paddle.x - self.paddle.width / 2.0
        px2 = self.paddle.x + self.paddle.width / 2.0
        py1 = self.paddle.y - self.paddle.height / 2.0
        py2 = self.paddle.y + self.paddle.height / 2.0
        closest_x = max(px1, min(b.x, px2))
        closest_y = max(py1, min(b.y, py2))
        dx = b.x - closest_x
        dy = b.y - closest_y
        return dx * dx + dy * dy <= b.radius * b.radius
