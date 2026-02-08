from typing import Optional, Dict, Any, List


class IUserStorage:
    """Interface for user storage"""

    async def initialize_connection(self) -> None:
        """Initialize the connection"""
        ...

    async def close_connection(self) -> None:
        """Close all connections"""
        ...

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve user"""
        ...

    async def user_exists(self, username: str) -> bool:
        """Check if username exists"""
        ...

    async def create_user(self, username: str, email: str, password_salt: str, password_hash: str) -> None:
        """Create new user with hashed password"""
        ...


class ICollectionStorage:
    """Interface for user's cards collection storage"""

    async def initialize_connection(self) -> None:
        """Initialize the connection"""
        ...

    async def close_connection(self) -> None:
        """Close all connections"""
        ...

    async def get_user_complete_collection(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve the user's entire card collection"""
        ...

    async def get_user_collection_sample(self, username: str, page: int, limit: int) -> Optional[Dict[str, Any]]:
        """Retrieve a sample of the user's card collection"""
        ...

    async def add_to_collection(self, user_id: int, card_id: int) -> None:
        """Adds a card to the user's collection"""
        ...


class IRiskGameStorage:
    """Interface for risk game's storage"""

    async def initialize_connection(self) -> None:
        """Initialize the connection"""
        ...

    async def close_connection(self) -> None:
        """Close all connections"""
        ...

    async def insert_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Insert score into table"""
        ...

    async def get_user_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user score from table"""
        ...

    async def update_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Updates user score"""
        ...

    async def user_exists(self, user_id: int) -> bool:
        """Checks if user exists in table"""
        ...

    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get users scores from table"""
        ...


class ISnakeGameStorage:
    """Interface for snake game's storage"""

    async def initialize_connection(self) -> None:
        """Initialize the connection"""
        ...

    async def close_connection(self) -> None:
        """Close all connections"""
        ...

    async def insert_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Insert score into table"""
        ...

    async def get_user_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user score from table"""
        ...

    async def update_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Updates user score"""
        ...

    async def user_exists(self, user_id: int) -> bool:
        """Checks if user exists in table"""
        ...

    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get users scores from table"""
        ...


class IDribbleKingStorage:
    """Interface for dribble king's storage"""

    async def initialize_connection(self) -> None:
        """Initialize the connection"""
        ...

    async def close_connection(self) -> None:
        """Close all connections"""
        ...

    async def insert_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Insert score into table"""
        ...

    async def get_user_score(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user score from table"""
        ...

    async def update_user_score(self, user_id: int, score: int, high_score: int) -> None:
        """Updates user score"""
        ...

    async def user_exists(self, user_id: int) -> bool:
        """Checks if user exists in table"""
        ...

    async def get_scores(self, limit: int) -> Optional[List[Dict[str, Any]]]:
        """Get users scores from table"""
        ...


class IPredictionStorage:
    """Interface for prediction storage"""

    async def initialize_connection(self) -> None:
        """Initialize the connection"""
        ...

    async def close_connection(self) -> None:
        """Close all connections"""
        ...

    async def get_elo(self, team: str) -> Dict[str, Any]:
        """Get elo score for team"""
        ...

    async def get_all_predictions(self) -> Optional[List[Dict[str, Any]]]:
        """Returns all predictions"""
        ...

    async def insert_prediction(
            self, match_id: int, model: str, home_id: int, home_xg: float, away_id: int,
            away_xg: float, home_p: float, draw_p: float, away_p: float, home_name: str, away_name: str) -> bool:
        """Adds new prediction to storage"""
        ...

    async def update_prediction_with_score(self, match_id: int, home_score, away_score) -> bool:
        """Updates match with actual score"""
        ...
