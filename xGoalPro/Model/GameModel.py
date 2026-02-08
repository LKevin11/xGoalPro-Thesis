from PyQt5.QtCore import QObject
from abc import ABCMeta, abstractmethod


class MetaQObjectABC(type(QObject), ABCMeta):
    """A metaclass combining PyQt5 QObject and Python's abstract base class (ABC) support.

    This allows the creation of QObject subclasses that can also define abstract methods,
    ensuring that derived classes implement required functionality while still benefiting
    from Qt's signal/slot mechanism.
    """
    pass


class GameModel(QObject, metaclass=MetaQObjectABC):
    """Base class for game models that require asynchronous cleanup.

    Inherits from QObject to integrate with PyQt5 and uses MetaQObjectABC as the metaclass
    to allow abstract method definitions in a QObject subclass.

    Methods:
        cleanup: Abstract method for performing asynchronous cleanup operations, 
                 such as closing persistence connections.
    """

    @abstractmethod
    async def cleanup(self) -> None:
        """Perform asynchronous cleanup operations.

        This method must be implemented by subclasses to close any open
        resources, such as database connections or API sessions.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        pass
