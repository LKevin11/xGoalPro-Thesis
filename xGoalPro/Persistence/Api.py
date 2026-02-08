import aiohttp
from io import BytesIO
from PIL import Image
from typing import Dict, Any, Optional


class IApi:
    """Interface for a generic API client."""
    async def get(self, endpoint: str, params: dict = None):
        """Perform a GET request."""
        raise NotImplementedError

    async def post(self, endpoint: str, data: dict = None):
        """Perform a POST request."""
        raise NotImplementedError


class FutApi(IApi):
    """API client for FUT (FIFA Ultimate Team) API, supporting JSON and image responses."""

    def __init__(self, base_url: str, token: str):
        """
        Initializes the FUT API client.

        Args:
            base_url: Base URL of the FUT API.
            token: Authentication token for API access.
        """
        self.__base_url: str = base_url.rstrip("/")
        self.__headers: dict = {
            "X-AUTH-TOKEN": token,
            "accept": "image/png"}

    async def get(self, endpoint: str, params: Optional[dict] = None):
        """
        Sends a GET request to the FUT API.

        Returns:
            If the response is an image, returns a PIL.Image object.
            Otherwise, returns the parsed JSON data.
        """
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.get(f"{self.__base_url}/{endpoint.lstrip('/')}", params=params) as resp:
                resp.raise_for_status()
                content_type = resp.headers.get("Content-Type", "")
                data = await resp.read()
                if "image" in content_type:
                    return Image.open(BytesIO(data))
                return await resp.json()

    async def post(self, endpoint: str, data: dict = None):
        """POST method is not implemented for FUT API."""
        pass


class PredictionApi(IApi):
    """API client for prediction services returning JSON data."""
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initializes the Prediction API client.

        Args:
            base_url: Base URL of the prediction API.
            headers: Optional HTTP headers to include in requests.
        """
        self.__base_url: str = base_url.rstrip('/')
        self.__headers: dict = headers or {}

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None):
        """
        Sends a GET request to the prediction API.

        Returns:
            Parsed JSON response.
        """
        url = f"{self.__base_url}/{endpoint.lstrip('/')}"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None):
        """
        Sends a POST request to the prediction API.

        Returns:
            Parsed JSON response.
        """
        url = f"{self.__base_url}/{endpoint.lstrip('/')}"
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.post(url, json=data) as response:
                response.raise_for_status()
                return await response.json()
