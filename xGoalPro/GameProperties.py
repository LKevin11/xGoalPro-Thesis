from Controllers.Minigame.BaseGameController import BaseGameController
from typing import Optional, Callable


class GameProperties:
    def __init__(self, controller, name, description, image, factory=None):
        self.controller: Optional[BaseGameController] = controller
        self.name: str = name
        self.description: str = description
        self.image: str = image
        self.factory: Optional[Callable] = factory
