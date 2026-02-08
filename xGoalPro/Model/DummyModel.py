from Model.GameModel import GameModel


class DummyModel(GameModel):
    """A placeholder implementation of GameModel for testing or development purposes.

    This model inherits from GameModel but does not implement any actual game logic.
    It can be used in situations where a minimal or dummy implementation is required.
    """

    def __init__(self):
        """Initialize the DummyModel by calling the parent GameModel constructor."""
        super().__init__()

    async def cleanup(self) -> None:
        """Perform cleanup operations.

        This is a stub method in DummyModel and does not perform any actions.
        It exists to satisfy the GameModel interface.
        """
        pass
