import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientResponseError
from Model.FUTModel import FUTModel


# -------------------------
# FIXTURES
# -------------------------
@pytest.fixture
def mock_api():
    return AsyncMock()


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.initialize_connection.return_value = None
    storage.add_to_collection.return_value = None
    storage.get_user_complete_collection.return_value = []
    storage.get_user_collection_sample.return_value = []
    storage.close_connection.return_value = None
    return storage


@pytest.fixture
def model(mock_storage, mock_api):
    return FUTModel(mock_storage, mock_api)


# -------------------------
# TEST: open_pack (success)
# -------------------------
@pytest.mark.asyncio
async def test_open_pack_success(model, mock_storage, mock_api):
    fake_image = MagicMock()
    fake_image.save.side_effect = lambda buf, format=None: buf.write(b"fakeimage")
    mock_api.get.return_value = fake_image

    with patch("random.randint", return_value=20):
        ok, data = await model.open_pack("user", 1)

    assert ok
    assert isinstance(data[0], bytes)
    mock_storage.add_to_collection.assert_awaited_once_with(1, 20)


# -------------------------
# TEST: open_pack (rate limit)
# -------------------------
@pytest.mark.asyncio
async def test_open_pack_rate_limit(model, mock_api):
    mock_api.get.side_effect = ClientResponseError(None, None, status=429)
    ok, msg = await model.open_pack("user", 1)
    assert not ok
    assert "Too many requests" in msg[0]


# -------------------------
# TEST: open_pack (exception)
# -------------------------
@pytest.mark.asyncio
async def test_open_pack_exception(model, mock_api):
    mock_api.get.side_effect = Exception("boom")
    ok, msg = await model.open_pack("user", 1)
    assert not ok
    assert "boom" in msg[0]


# -------------------------
# TEST: fetching_cards (success)
# -------------------------
@pytest.mark.asyncio
async def test_fetching_cards_success(model, mock_storage, mock_api):
    mock_storage.get_user_complete_collection.return_value = [{"card_id": 1}, {"card_id": 2}]
    mock_storage.get_user_collection_sample.return_value = [{"card_id": 10}, {"card_id": 11}]
    fake_image = MagicMock()
    fake_image.save.side_effect = lambda buf, format=None: buf.write(b"fakeimage")
    mock_api.get.return_value = fake_image

    ok, data = await model.fetching_cards("user", 1)
    assert ok
    assert len(data) == 2
    assert all(isinstance(x, bytes) for x in data)


# -------------------------
# TEST: fetching_cards (exception)
# -------------------------
@pytest.mark.asyncio
async def test_fetching_cards_exception(model, mock_storage, mock_api):
    # Make sure API is called at least once
    mock_storage.get_user_complete_collection.return_value = [{"card_id": 1}]
    mock_storage.get_user_collection_sample.return_value = [{"card_id": 10}]
    mock_api.get.side_effect = Exception("fail")

    ok, msg = await model.fetching_cards("user", 1)
    assert not ok
    assert "fail" in msg[0]


# -------------------------
# TEST: cleanup
# -------------------------
@pytest.mark.asyncio
async def test_cleanup(model, mock_storage):
    await model.cleanup()
    mock_storage.close_connection.assert_awaited_once()
