import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock, patch
from aiohttp import ClientResponseError
from Model.StatisticsModel import StatisticsModel
from datetime import date

# -------------------------
# FIXTURES
# -------------------------
@pytest.fixture
def mock_api():
    api = AsyncMock()
    return api

@pytest.fixture
def mock_loader():
    loader = AsyncMock()
    return loader

@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.get_all_predictions.return_value = [{"match_id": 1, "home_name": "TeamA"}]
    return storage

@pytest.fixture
def model(mock_api, mock_loader, mock_storage):
    m = StatisticsModel(mock_api, mock_loader, mock_storage)
    m.add_league("PL", "Premier League")
    return m

# -------------------------
# TEST: add_league
# -------------------------
def test_add_league(model):
    model.add_league("SA", "Serie A")
    assert "SA" in model._StatisticsModel__leagues
    assert model._StatisticsModel__leagues["SA"] == "Serie A"

# -------------------------
# TEST: fetch_leagues
# -------------------------
@pytest.mark.asyncio
async def test_fetch_leagues_success(model, mock_api):
    mock_api.get.return_value = {
        "competitions": [
            {"id": 1, "name": "Premier League", "code": "PL", "emblem": "http://img1.png"},
            {"id": 2, "name": "Serie A", "code": "SA", "emblem": "http://img2.png"},
        ]
    }
    fake_bytes = b"image-bytes"

    async def mock_read():
        return fake_bytes

    async with patch("aiohttp.ClientSession.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.__aenter__.return_value.read = mock_read
        ok, data = await model.fetch_leagues()

    assert ok
    assert data[0]["code"] == "PL"
    assert data[0]["emblem"] == fake_bytes

@pytest.mark.asyncio
async def test_fetch_leagues_rate_limit(model, mock_api):
    mock_api.get.side_effect = ClientResponseError(None, None, status=429)
    ok, msg = await model.fetch_leagues()
    assert not ok
    assert "Too many requests" in msg[0]

@pytest.mark.asyncio
async def test_fetch_leagues_exception(model, mock_api):
    mock_api.get.side_effect = Exception("Network down")
    ok, msg = await model.fetch_leagues()
    assert not ok
    assert "Network down" in msg[0]

# -------------------------
# TEST: fetch_league_statistics
# -------------------------
@pytest.mark.asyncio
async def test_fetch_leagues_success(model, mock_api):
    # Mock the API return value
    mock_api.get.return_value = {
        "competitions": [
            {"id": 1, "name": "Premier League", "code": "PL", "emblem": "http://img1.png"},
            {"id": 2, "name": "Serie A", "code": "SA", "emblem": "http://img2.png"},
        ]
    }

    fake_bytes = b"image-bytes"

    # Patch the internal image fetch method to avoid real HTTP calls
    with patch.object(model, "_StatisticsModel__fetch_image", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = fake_bytes
        ok, data = await model.fetch_leagues()

    assert ok
    assert data[0]["code"] == "PL"
    assert data[0]["emblem"] == fake_bytes


@pytest.mark.asyncio
async def test_fetch_league_statistics_exception(model, mock_api):
    mock_api.get.side_effect = Exception("API fail")
    ok, msg = await model.fetch_league_statistics("PL")
    assert not ok
    assert "API fail" in msg[0]

# -------------------------
# TEST: fetch_team_statistics
# -------------------------
@pytest.mark.asyncio
async def test_fetch_team_statistics_success(model):
    fake_team_data = {"id": 1, "name": "TeamA"}
    fake_matches = {"matches": []}

    with patch.object(model._StatisticsModel__league_api, "get", side_effect=[fake_team_data, fake_matches]):
        ok, data = await model.fetch_team_statistics(1)

    assert ok
    team_data, results = data
    assert team_data == fake_team_data
    assert isinstance(results, list)

@pytest.mark.asyncio
async def test_fetch_team_statistics_exception(model, mock_api):
    mock_api.get.side_effect = Exception("Team API down")
    ok, msg = await model.fetch_team_statistics(1)
    assert not ok
    assert "Team API down" in msg[0]

# -------------------------
# TEST: fetch_predictions
# -------------------------
@pytest.mark.asyncio
async def test_fetch_predictions_success(model, mock_storage):
    ok, data = await model.fetch_predictions()
    assert ok
    assert data[0]["match_id"] == 1

@pytest.mark.asyncio
async def test_fetch_predictions_exception(model, mock_storage):
    mock_storage.get_all_predictions.side_effect = Exception("DB fail")
    ok, msg = await model.fetch_predictions()
    assert not ok
    assert "DB fail" in msg[0]

# -------------------------
# TEST: cleanup
# -------------------------
@pytest.mark.asyncio
async def test_cleanup(model, mock_storage):
    await model.cleanup()
    mock_storage.close_connection.assert_awaited_once()
