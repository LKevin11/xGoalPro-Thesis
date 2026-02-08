import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import AsyncMock
from Model.SnakeGameModel import SnakeGameModel


# -------------------------
# FIXTURES
# -------------------------
@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.initialize_connection.return_value = None
    storage.close_connection.return_value = None
    storage.user_exists.return_value = False
    storage.get_user_score.return_value = {"score": 10, "high_score": 20}
    storage.get_scores.return_value = [
        {"username": "Alice", "high_score": 100},
        {"username": "Bob", "high_score": 80},
    ]
    return storage


@pytest.fixture
def model(mock_storage):
    return SnakeGameModel(mock_storage)


# -------------------------
# TEST: init_state (new user)
# -------------------------
@pytest.mark.asyncio
async def test_init_state_new_user(model, mock_storage):
    mock_storage.user_exists.return_value = False
    await model.init_state(1)
    mock_storage.insert_user_score.assert_awaited_once_with(1, 0, 0)
    assert model.score == 0
    assert model.high_score == 0


# -------------------------
# TEST: init_state (existing user)
# -------------------------
@pytest.mark.asyncio
async def test_init_state_existing_user(model, mock_storage):
    mock_storage.user_exists.return_value = True
    await model.init_state(1)
    mock_storage.get_user_score.assert_awaited_once_with(1)
    assert model.score == 10
    assert model.high_score == 20


# -------------------------
# TEST: init_state (exception)
# -------------------------
@pytest.mark.asyncio
async def test_init_state_exception(model, mock_storage):
    mock_storage.user_exists.side_effect = Exception("DB fail")
    ok, msg = await model.init_state(1)
    assert not ok
    assert "DB fail" in msg[0]


# -------------------------
# TEST: save_score
# -------------------------
@pytest.mark.asyncio
async def test_save_score(model, mock_storage):
    model.score = 50
    model.high_score = 100
    await model.save_score(1)
    mock_storage.update_user_score.assert_awaited_once_with(1, 50, 100)


# -------------------------
# TEST: get_leaderboard
# -------------------------
@pytest.mark.asyncio
async def test_get_leaderboard(model, mock_storage):
    leaderboard = await model.get_leaderboard(2)
    assert leaderboard[0] == (1, "Alice", 100)
    assert leaderboard[1] == (2, "Bob", 80)


# -------------------------
# TEST: cleanup
# -------------------------
@pytest.mark.asyncio
async def test_cleanup(model, mock_storage):
    await model.cleanup()
    mock_storage.close_connection.assert_awaited_once()
