from Model.GameModel import GameModel
from Persistence.StorageInterface import IDribbleKingStorage
from typing import Tuple, List, Any, Optional, Dict

import random
import time
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtCore import QRectF
from Assets.utils import lane_to_x, WINDOW_H, PLAYER_Y, LANES


class Obstacle:
    """Represents a single obstacle in the Dribble King game.

    Attributes:
        lane (int): Lane index where the obstacle is located.
        y (float): Vertical position of the obstacle.
        passed (bool): Whether the obstacle has been passed by the player.
        __w (int): Width of the obstacle (internal use).
        __h (int): Height of the obstacle (internal use).
    """
    def __init__(self, lane, y, w=120, h=120):

        self.__w: int = w
        self.__h: int = h

        self.lane: int = lane
        self.y: float = y
        self.passed: bool = False

    def rect(self):
        """Get the QRectF representing the obstacle's position and size.

        Returns:
            QRectF: Rectangle for collision detection and rendering.
        """
        lane_x = lane_to_x(self.lane)
        return QRectF(lane_x - self.__w/2, self.y - self.__h/2, self.__w, self.__h)


class DribbleKingModel(GameModel):
    """Model for the Dribble King game.

    Handles player movement between lanes, ball physics, obstacle spawning,
    collision detection, scoring, and high score tracking. Updates are
    emitted via a PyQt signal.

    Signals:
        updated: Emitted when the model state changes (used to refresh the UI).

    Attributes:
        lane (int): Current player lane.
        ball_offset (float): Vertical offset for the bouncing ball.
        ball_radius (float): Radius of the ball used for collision.
        obstacles (List[Obstacle]): List of obstacles in the current game.
        score (int): Current score for the game session.
        game_over (bool): True if the player has collided with an obstacle.
        timer (QTimer): Timer driving game loop updates.
    """
    updated = pyqtSignal()   # emitted when model changes

    def __init__(self, storage):
        super().__init__()

        self.__storage: IDribbleKingStorage = storage
        self.__high_score: int = 0
        self.__start_time: float = 0.0
        self.__ball_vel: float = 0.0
        self.__speed: float = 2.2
        self.__spawn_timer: float = 0.0
        self.__spawn_interval: int = 900

        self.lane: int = 1
        self.ball_offset: float = 0.0
        self.ball_radius: float = 50
        self.obstacles: list = []
        self.score: int = 0
        self.game_over: bool = False
        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self.__step)

        self.reset()

    def start(self) -> None:
        """Start a new game, resetting the state and starting the update timer."""
        self.reset()
        self.__start_time = time.time()
        self.timer.start(16)

    async def init_state(self, user_id: int) -> Tuple[bool, List[Any]]:
        """Initialize player state from storage.

        Args:
            user_id (int): Unique identifier for the player.

        Returns:
            Tuple[bool, List[Any]]: Success status and optional error messages.
        """
        try:
            await self.__storage.initialize_connection()
            user_exists = await self.__storage.user_exists(user_id)

            if user_exists:
                user_data = await self.__storage.get_user_score(user_id)
                if user_data:
                    self.__high_score = user_data.get('high_score', 0)
                else:
                    # In case riskScore row is missing, create one
                    await self.__storage.insert_user_score(user_id, 0, 0)
                    self.score = 0
                    self.__high_score = 0
            else:
                await self.__storage.insert_user_score(user_id, 0, 0)
                self.score = 0
                self.__high_score = 0

            return True, []
        except Exception as e:
            return False, [str(e)]

    async def save_score(self, user_id: int) -> None:
        """Save the current score and high score for the player.

        Args:
            user_id (int): Unique identifier for the player.
        """
        await self.__storage.update_user_score(user_id, self.score, self.__high_score)

    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve top scores from storage.

        Args:
            limit (int): Maximum number of high scores to return.

        Returns:
            Optional[List[Dict[str, Any]]]: List of high scores, each with username and score.
        """
        return await self.__storage.get_scores(limit)

    def reset(self) -> None:
        """Reset the game state to initial values, clearing obstacles and score."""
        self.__start_time = time.time()
        self.lane = 1
        self.ball_offset = 0.0
        self.__ball_vel = 0.0
        self.ball_radius = 50
        self.score = 0
        self.__speed = 2.2
        self.obstacles = []
        self.__spawn_timer = 0.0
        self.__spawn_interval = 900
        self.game_over = False

    async def cleanup(self) -> None:
        """Clean up resources and close storage connections."""
        await self.__storage.close_connection()

    def __step(self, dt=None) -> None:
        """Update the game state for each timer tick.

        Handles obstacle spawning, ball physics, collision detection,
        scoring, and game-over conditions.

        Args:
            dt (float, optional): Time elapsed since last update in milliseconds.
        """
        if self.game_over:
            self.timer.stop()
            return

        if dt is None:
            dt = self.timer.interval()

        elapsed = time.time() - self.__start_time
        self.__speed = 2.2 + (elapsed / 20.0)

        # spawn obstacles
        self.__spawn_timer += dt
        if self.__spawn_timer >= self.__spawn_interval:
            self.__spawn_timer = 0
            self.__spawn_interval = max(450, 900 - int(elapsed * 20))
            lane = random.randrange(0, LANES)
            self.obstacles.append(Obstacle(lane, -80))

        # move obstacles
        for obs in self.obstacles:
            obs.y += self.__speed * (dt/16.0) * 6
            if (not obs.passed) and (obs.y > PLAYER_Y + 40):
                obs.passed = True
                self.score += 10
                if self.score > self.__high_score:
                    self.__high_score = self.score

        self.obstacles = [o for o in self.obstacles if o.y < WINDOW_H + 200]

        # ball physics
        if self.ball_offset <= 0 and random.random() < 0.02:
            self.__ball_vel = -6.0
        self.__ball_vel += 0.35
        self.ball_offset += self.__ball_vel
        if self.ball_offset > 0:
            self.ball_offset = 0
            self.__ball_vel *= -0.42
            if abs(self.__ball_vel) < 1.0:
                self.__ball_vel = 0

        # collision
        for obs in self.obstacles:
            if obs.lane == self.lane:
                player_ball_y = PLAYER_Y - self.ball_radius + self.ball_offset
                obs_rect = obs.rect()
                cx = lane_to_x(self.lane)
                cy = player_ball_y
                rx = max(obs_rect.left(), min(cx, obs_rect.right()))
                ry = max(obs_rect.top(), min(cy, obs_rect.bottom()))
                dist_sq = (rx - cx) ** 2 + (ry - cy) ** 2
                if dist_sq < self.ball_radius ** 2:
                    self.game_over = True
                    break

        self.updated.emit()
