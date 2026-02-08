import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from Model.PredictionModel import PredictionModel
from aiohttp import ClientResponseError


# -------------------------
# FIXTURES
# -------------------------
@pytest.fixture
def mock_api():
    api = AsyncMock()
    return api


@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.get_elo.return_value = 1500.0
    storage.insert_prediction.return_value = True
    return storage


@pytest.fixture
def mock_models():
    return {"m1": ("home.pkl", "away.pkl")}


@pytest.fixture
def model(mock_api, mock_storage, mock_models):
    return PredictionModel(mock_api, mock_storage, mock_models)


# -------------------------
# TEST: add_league
# -------------------------
def test_add_league(model):
    model.add_league("PL")
    assert "PL" in model._PredictionModel__leagues


# -------------------------
# TEST: fetch_leagues (success)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_leagues_success(model, mock_api):
    model.add_league("PL")

    mock_api.get.return_value = {
        "competitions": [
            {"id": 1, "name": "Premier League", "code": "PL", "emblem": "http://emblem.png"},
            {"id": 2, "name": "Serie A", "code": "SA", "emblem": "http://emblem2.png"},
        ]
    }

    fake_bytes = b"image"
    mock_resp = AsyncMock()
    mock_resp.read.return_value = fake_bytes
    with patch("aiohttp.ClientSession.get", return_value=mock_resp) as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_resp
        ok, data = await model.fetch_leagues()

    assert ok
    assert data[0]["name"] == "Premier League"
    assert data[0]["emblem"] == fake_bytes


# -------------------------
# TEST: fetch_leagues (HTTP 429)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_leagues_too_many_requests(model, mock_api):
    mock_api.get.side_effect = ClientResponseError(None, None, status=429)
    ok, msg = await model.fetch_leagues()
    assert not ok
    assert "Too many requests" in msg[0]


# -------------------------
# TEST: fetch_teams (success)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_teams_success(model, mock_api):
    mock_api.get.return_value = {
        "standings": [{
            "table": [
                {"team": {"id": 1, "shortName": "TeamA", "crest": "http://crest.png"}}
            ]
        }],
        "competition": {"name": "LeagueName"}
    }

    fake_bytes = b"crest"
    mock_resp = AsyncMock()
    mock_resp.read.return_value = fake_bytes
    with patch("aiohttp.ClientSession.get", return_value=mock_resp) as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_resp
        ok, (teams, comp_name) = await model.fetch_teams("PL")

    assert ok
    assert teams[0]["name"] == "TeamA"
    assert comp_name == "LeagueName"


# -------------------------
# TEST: fetch_teams (Exception)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_teams_exception(model, mock_api):
    mock_api.get.side_effect = Exception("API error")
    ok, msg = await model.fetch_teams("PL")
    assert not ok
    assert "API error" in msg[0]


# -------------------------
# TEST: fetch_matches (success)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_matches_success(model, mock_api):
    mock_api.get.return_value = {
        "matches": [
            {"id": 1, "utcDate": "2025-01-01", "competition": {"name": "Comp"},
             "homeTeam": {"id": 1, "shortName": "H", "crest": "http://home.png"},
             "awayTeam": {"id": 2, "shortName": "A", "crest": "http://away.png"}}
        ]
    }

    fake_bytes = b"crest"
    mock_resp = AsyncMock()
    mock_resp.read.return_value = fake_bytes
    with patch("aiohttp.ClientSession.get", return_value=mock_resp) as mock_get:
        mock_get.return_value.__aenter__.return_value = mock_resp
        ok, data = await model.fetch_matches(1)

    assert ok
    assert data[0]["home_name"] == "H"
    assert data[0]["away_name"] == "A"


# -------------------------
# TEST: fetch_matches (HTTP 429)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_matches_rate_limit(model, mock_api):
    mock_api.get.side_effect = ClientResponseError(None, None, status=429)
    ok, msg = await model.fetch_matches(1)
    assert not ok
    assert "Too many requests" in msg[0]


# -------------------------
# TEST: fetch_h2h (success)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_h2h_success(model, mock_api, mock_models):
    mock_api.get.return_value = {
        "matches": [
            {"competition": {"name": "C"},
             "utcDate": "2025-01-01",
             "homeTeam": {"shortName": "H"},
             "awayTeam": {"shortName": "A"},
             "score": {"fullTime": {"home": 1, "away": 0}}}
        ]
    }

    ok, data = await model.fetch_h2h(10)
    assert ok
    match_list, models = data
    assert match_list[0]["homeTeam"] == "H"
    assert models == mock_models


# -------------------------
# TEST: fetch_h2h (exception)
# -------------------------
@pytest.mark.asyncio
async def test_fetch_h2h_exception(model, mock_api):
    mock_api.get.side_effect = Exception("fail")
    ok, msg = await model.fetch_h2h(10)
    assert not ok
    assert "fail" in msg[0]


# -------------------------
# TEST: predict_scores (success)
# -------------------------
@pytest.mark.asyncio
async def test_predict_scores_success(model, mock_api, mock_storage):
    mock_api.get.side_effect = [
        {"homeTeam": {"shortName": "H"}, "awayTeam": {"shortName": "A"}},  # match
        {"matches": [{"status": "FINISHED", "homeTeam": {"id": 1}, "awayTeam": {"id": 2},
                      "score": {"fullTime": {"home": 2, "away": 1}}}]},     # home matches
        {"matches": [{"status": "FINISHED", "homeTeam": {"id": 2}, "awayTeam": {"id": 3},
                      "score": {"fullTime": {"home": 0, "away": 0}}}]}      # away matches
    ]

    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = np.array([[0.1]])
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([1.0])

    with patch("joblib.load", side_effect=[mock_scaler, mock_model, mock_model]):
        ok, pred = await model.predict_scores(1, 2, 123, [1])

    assert ok
    assert "Expected_Home_Goals" in pred
    mock_storage.insert_prediction.assert_awaited_once()


# -------------------------
# TEST: predict_scores (rate limit)
# -------------------------
@pytest.mark.asyncio
async def test_predict_scores_rate_limit(model, mock_api):
    mock_api.get.side_effect = ClientResponseError(None, None, status=429)
    ok, msg = await model.predict_scores(1, 2, 123, [1])
    assert not ok
    assert "Too many requests" in msg[0]


# -------------------------
# TEST: predict_scores (generic exception)
# -------------------------
@pytest.mark.asyncio
async def test_predict_scores_generic_exception(model, mock_api):
    mock_api.get.side_effect = Exception("boom")
    ok, msg = await model.predict_scores(1, 2, 123, [1])
    assert not ok
    assert "boom" in msg[0]


# -------------------------
# TEST: cleanup
# -------------------------
@pytest.mark.asyncio
async def test_cleanup(model, mock_storage):
    await model.cleanup()
    mock_storage.close_connection.assert_awaited_once()
