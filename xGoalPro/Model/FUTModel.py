from Model.GameModel import GameModel

from Persistence.StorageInterface import ICollectionStorage
from Persistence.Api import IApi

from typing import Tuple, List, Any
import random
from io import BytesIO
import aiohttp


class FUTModel(GameModel):
    """FUT (FIFA Ultimate Team) model handling card collection operations.

    This model interacts with a persistence storage layer and an API to manage
    user card collections, open packs, and fetch card images. It supports
    pagination for browsing collections.

    Attributes:
        storage (ICollectionStorage): Interface for collection storage operations.
        api (IApi): Interface for retrieving card images from an external API.
        page (int): Current page in paginated collection view.
        limit (int): Number of cards per page.
        total (int): Total number of cards owned by the user.
    """

    def __init__(self, storage, api):
        """Initialize FUTModel with storage and API interfaces.

        Args:
            storage (ICollectionStorage): Storage interface for user collections.
            api (IApi): API interface for fetching card images.
        """
        super().__init__()

        self.storage: ICollectionStorage = storage
        self.api: IApi = api
        self.page = 1
        self.limit = 6
        self.total = 0

    async def open_pack(self, username, user_id) -> Tuple[bool, List[Any]]:
        """Open a new pack for the user, adding a random card to their collection.

        Ensures no duplicate cards are added and returns the image bytes of the new card.

        Args:
            username (str): Username of the player opening the pack.
            user_id (int): ID of the player in the database.

        Returns:
            Tuple[bool, List[Any]]: 
                - success (bool): True if a new card was added successfully.
                - data (List[Any]): Either the image bytes of the new card or error messages.
        """

        try:

            await self.storage.initialize_connection()

            collection_rows = await self.storage.get_user_complete_collection(username)

            existing_card_ids = set()
            if collection_rows:
                for row in collection_rows:
                    existing_card_ids.add(row['card_id'])

            max_card_id = 17736
            attempts = 0
            max_attempts = 50

            while attempts < max_attempts:
                random_card_id = random.randint(0, max_card_id)
                if random_card_id not in existing_card_ids:
                    break
                attempts += 1
            else:
                return False, ["No new cards available or collection is complete"]

            image = await self.api.get(f"{random_card_id}/image")
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            image_bytes = buffer.getvalue()

            await self.storage.add_to_collection(user_id, random_card_id)

            return True, [image_bytes]
        
        except aiohttp.ClientResponseError as e:
            return False, ["Too many requests"]

        except Exception as e:
            return False, [str(e)]

    async def fetching_cards(self, name: str, direction: int) -> Tuple[bool, List[Any]]:
        """Fetch a paginated sample of card images from the user's collection.

        Args:
            name (str): Username of the player.
            direction (int): Direction to move the page (1 for next, -1 for previous).

        Returns:
            Tuple[bool, List[Any]]:
                - success (bool): True if cards were successfully fetched.
                - data (List[Any]): List of card image bytes or error messages.
        """
        try:

            await self.storage.initialize_connection()
            await self.update_total(name)

            total_pages = (self.total + self.limit - 1) // self.limit if self.total > 0 else 1
            self.update_page(total_pages, direction)

            collection_cards_sample = await self.storage.get_user_collection_sample(name, self.page, self.limit)

            card_ids = []
            if collection_cards_sample:
                for row in collection_cards_sample:
                    card_ids.append(row['card_id'])

            return_values = []
            for ids in card_ids:
                image = await self.api.get(f"{ids}/image")
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()
                return_values.append(image_bytes)

            return True, return_values
        
        except aiohttp.ClientResponseError as e:
            return False, ["Too many requests"]

        except Exception as e:
            return False, [str(e)]

    async def update_total(self, username: str) -> None:
        """Update the total number of cards the user owns.

        Args:
            username (str): Username of the player.

        Side effects:
            Updates self.total with the current number of cards in the user's collection.
        """
        collection_rows = await self.storage.get_user_complete_collection(username)
        if collection_rows:
            self.total = len(collection_rows)
        else:
            self.total = 0

    def update_page(self, total_pages: int, direction: int) -> None:
        """Update the current page within valid bounds.

        Args:
            total_pages (int): Total number of pages available.
            direction (int): Direction to move the page (1 for next, -1 for previous).

        Side effects:
            Updates self.page if the new page is within valid bounds.
        """
        new_page = self.page + direction
        if 1 <= new_page <= total_pages:
            self.page = new_page

    def can_go_prev(self) -> bool:
        """Check if it is possible to go to the previous page.

        Returns:
            bool: True if the current page is greater than 1.
        """
        return self.page > 1

    def can_go_next(self) -> bool:
        """Check if it is possible to go to the next page.

        Returns:
            bool: True if the current page is less than the total number of pages.
        """
        total_pages = (self.total + self.limit - 1) // self.limit if self.total > 0 else 1
        return self.page < total_pages

    async def cleanup(self):
        """Close the storage connection and perform cleanup operations.

        Should be called when the FUTModel instance is no longer needed.
        """
        await self.storage.close_connection()
