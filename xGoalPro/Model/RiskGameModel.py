import random
from typing import Tuple, List, Any, Optional, Dict

from Model.GameModel import GameModel

from Persistence.StorageInterface import IRiskGameStorage


class RiskGameModel(GameModel):
    """Model for a Risk-style game where players advance and accumulate points with risk of being tackled.

    Tracks the user's current attack progress, long-term bank, and high score. 
    Interacts with a persistence storage interface to save and load scores.

    Attributes:
        __storage (IRiskGameStorage): Storage interface for retrieving and updating user scores.
        bank (int): Long-term bank of points accumulated across attacks.
        high_score (int): Highest bank achieved by the user.
        position (int): Current position in meters from start (0) to goal (100) in the current attack.
        current (int): Points accumulated in the current attack.
        in_attack (bool): Whether the player is currently in an ongoing attack.
    """

    def __init__(self, storage):
        """Initialize RiskGameModel with a storage backend.

        Args:
            storage (IRiskGameStorage): Storage interface for storing and retrieving user scores.
        """
        super().__init__()
        self.__storage: IRiskGameStorage = storage
        self.bank: int = 0
        self.high_score: int = 0

        self.position = 0
        self.current = 0
        self.in_attack = True

        self.__attack_attempts = 0

    async def init_state(self, user_id: int) -> Tuple[bool, List[Any]]:
        """Initialize the user’s game state by loading scores or creating new records.

        Args:
            user_id (int): Unique ID of the player.

        Returns:
            Tuple[bool, List[Any]]: (success flag, errors list). Empty errors if successful.
        """
        try:
            await self.__storage.initialize_connection()
            user_exists = await self.__storage.user_exists(user_id)

            if user_exists:
                user_data = await self.__storage.get_user_score(user_id)
                if user_data:
                    self.bank = user_data.get('bank', 0)
                    self.high_score = user_data.get('high_score', 0)
                else:
                    # In case riskScore row is missing, create one
                    await self.__storage.insert_user_score(user_id, 0, 0)
                    self.bank = 0
                    self.high_score = 0
            else:
                await self.__storage.insert_user_score(user_id, 0, 0)
                self.bank = 0
                self.high_score = 0

            return True, []
        except Exception as e:
            return False, [str(e)]

    def reset_attack(self) -> None:
        """Reset the current attack progress, starting a new attack from position 0."""
        self.position = 0
        self.current = 0
        self.__attack_attempts = 0
        self.in_attack = True

    async def advance(self, user_id: int) -> tuple:
        """Attempt to advance in the current attack.

        Simulates a random meter gain. There is a probability of being tackled based on
        position and number of attempts, which causes loss of all banked and current points.
        Reaching position >= 100 triggers a goal with bonus points and auto-banking.

        Args:
            user_id (int): Unique ID of the player.

        Returns:
            Tuple[str, str]:
                - result: One of 'safe', 'banked', or 'tackled'.
                - msg: Descriptive message of what occurred in this attempt.
        """
        # Simulate meters gain
        meters = random.randint(5, 15)
        self.position += meters
        gained_points = meters  # 1 point per meter in current attack
        self.current += gained_points
        self.__attack_attempts += 1

        # Probability of being tackled increases with position and attempts.
        # base chance 5% + position*0.007 + attempts*0.03
        tackle_chance = 0.05 + (self.position * 0.007) + (self.__attack_attempts * 0.03)
        tackle_chance = min(tackle_chance, 0.95)

        roll = random.random()
        if roll < tackle_chance:
            # tackled: lose EVERYTHING (explicit requirement)
            lost_bank = self.bank
            self.bank = 0
            self.current = 0
            self.in_attack = False
            await self.__save_score(user_id)
            return 'tackled', f'Tackled! You lost everything (bank {lost_bank} reset to 0).'

        # if we reached the goal (position >=100), big reward and auto-bank
        if self.position >= 100:
            reward = int(self.current * 1.5)  # goal bonus
            self.current += reward
            self.bank += self.current
            if self.bank > self.high_score:
                self.high_score = self.bank
            await self.__save_score(user_id)
            msg = f'GOAL! You scored and banked {self.current} points (including bonus).'
            self.reset_attack()
            return 'banked', msg

        return 'safe', f'Advanced {meters} meters, gained {gained_points} points this attack.'

    async def hold(self, user_id: int) -> int:
        """Bank current attack points into long-term bank and start a new attack.

        Args:
            user_id (int): Unique ID of the player.

        Returns:
            int: Number of points banked from the current attack.
        """
        self.bank += self.current
        banked = self.current
        self.current = 0
        if self.bank > self.high_score:
            self.high_score = self.bank
        self.in_attack = False
        await self.__save_score(user_id)
        # Immediately start a new attack
        self.reset_attack()
        return banked

    async def reset_progress(self, user_id: int) -> None:
        """Reset the user’s bank and high score, and start a new attack.

        Args:
            user_id (int): Unique ID of the player.
        """
        self.bank = 0
        self.high_score = 0
        self.reset_attack()
        await self.__save_score(user_id)

    async def cleanup(self) -> None:
        """Close the storage connection and clean up resources."""
        await self.__storage.close_connection()

    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Retrieve the top scores from storage.

        Args:
            limit (int): Maximum number of scores to retrieve.

        Returns:
            Optional[List[Dict[str, Any]]]: List of top scores with user info.
        """
        return await self.__storage.get_scores(limit)

    async def __save_score(self, user_id: int) -> None:
        """Save the current bank and high score for the user to storage.

        Args:
            user_id (int): Unique ID of the player.
        """
        await self.__storage.update_user_score(user_id, self.bank, self.high_score)
