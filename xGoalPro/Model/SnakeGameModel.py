from Model.GameModel import GameModel
from Persistence.StorageInterface import ISnakeGameStorage
from typing import Optional, List, Tuple, Any


class SnakeGameModel(GameModel):
    """Model for a Snake game that tracks user scores and high scores.

    Interacts with a persistence storage interface to initialize state, save scores,
    and retrieve leaderboard information. Inherits from GameModel for consistency
    with other game models.
    
    Attributes:
        __storage (ISnakeGameStorage): Storage interface for user scores.
        score (int): Current score of the player.
        high_score (int): Highest score achieved by the player.
    """

    def __init__(self, storage):
        """Initialize SnakeGameModel with a storage backend.

        Args:
            storage (ISnakeGameStorage): Storage interface for storing and retrieving user scores.
        """

        super().__init__()

        self.__storage: ISnakeGameStorage = storage
        self.score = 0
        self.high_score = 0

    async def init_state(self, user_id: int) -> Optional[Tuple[bool, List[Any]]]:
        """Initialize the game state for a user by loading existing scores or creating new records.

        Args:
            user_id (int): The unique ID of the player.

        Returns:
            Optional[Tuple[bool, List[Any]]]: Returns (False, [error_message]) if an exception occurs,
            otherwise None. Sets `self.score` and `self.high_score`.
        """
        try:
            await self.__storage.initialize_connection()
            if await self.__storage.user_exists(user_id):
                data = await self.__storage.get_user_score(user_id)
                if data:
                    self.score = data.get("score", 0)
                    self.high_score = data.get("high_score", 0)
            else:
                await self.__storage.insert_user_score(user_id, 0, 0)
                self.score = 0
                self.high_score = 0
        except Exception as e:
            return False, [str(e)]

    async def save_score(self, user_id: int) -> None:
        """Save the current score and high score of the user to storage.

        Args:
            user_id (int): The unique ID of the player.
        """
        await self.__storage.update_user_score(user_id, self.score, self.high_score)

    async def get_leaderboard(self, limit: int = 10) -> list:
        """Retrieve the top players' leaderboard.

        Args:
            limit (int): Maximum number of leaderboard entries to return (default is 10).

        Returns:
            list: List of tuples in the format (rank, username, high_score).
        """
        data = await self.__storage.get_scores(limit)
        return [(i + 1, row["username"], row["high_score"]) for i, row in enumerate(data)]

    async def cleanup(self) -> None:
        """Close the storage connection and perform cleanup operations."""
        await self.__storage.close_connection()
