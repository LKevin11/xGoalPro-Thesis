import sys, os, pytest, random
from unittest.mock import AsyncMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Model.RiskGameModel import RiskGameModel


# -------------------------
# FIXTURES
# -------------------------
@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.initialize_connection.return_value = None
    storage.close_connection.return_value = None
    storage.user_exists.return_value = True
    storage.get_user_score.return_value = {"bank": 50, "high_score": 100}
    storage.get_scores.return_value = [
        {"username": "Alice", "high_score": 300},
        {"username": "Bob", "high_score": 200},
    ]
    return storage


@pytest.fixture
def model(mock_storage):
    return RiskGameModel(mock_storage)


# -------------------------
# TEST: init_state (existing user)
# -------------------------
@pytest.mark.asyncio
async def test_init_state_existing_user(model, mock_storage):
    ok, msg = await model.init_state(1)
    assert ok
    assert msg == []
    mock_storage.initialize_connection.assert_awaited_once()
    mock_storage.user_exists.assert_awaited_once_with(1)
    assert model.bank == 50
    assert model.high_score == 100


# -------------------------
# TEST: init_state (new user)
# -------------------------
@pytest.mark.asyncio
async def test_init_state_new_user(model, mock_storage):
    mock_storage.user_exists.return_value = False
    ok, msg = await model.init_state(1)
    assert ok
    mock_storage.insert_user_score.assert_awaited_once_with(1, 0, 0)
    assert model.bank == 0
    assert model.high_score == 0


# -------------------------
# TEST: init_state (exception)
# -------------------------
@pytest.mark.asyncio
async def test_init_state_exception(model, mock_storage):
    mock_storage.user_exists.side_effect = Exception("DB error")
    ok, msg = await model.init_state(1)
    assert not ok
    assert "DB error" in msg[0]


# -------------------------
# TEST: reset_attack
# -------------------------
def test_reset_attack(model):
    model.position = 50
    model.current = 30
    model.in_attack = False
    model._RiskGameModel__attack_attempts = 5
    model.reset_attack()
    assert model.position == 0
    assert model.current == 0
    assert model.in_attack
    assert model._RiskGameModel__attack_attempts == 0


# -------------------------
# TEST: advance — safe move
# -------------------------
@pytest.mark.asyncio
@patch("random.random", return_value=1.0)  # high roll → NOT tackled
@patch("random.randint", return_value=10)
async def test_advance_safe(mock_randint, mock_random, model, mock_storage):
    result, msg = await model.advance(1)
    assert result == "safe"
    assert "Advanced" in msg
    assert model.current > 0
    mock_storage.update_user_score.assert_not_called()


# -------------------------
# TEST: advance — tackled
# -------------------------
@pytest.mark.asyncio
@patch("random.random", return_value=0.0)  # low roll → tackled
@patch("random.randint", return_value=10)
async def test_advance_tackled(mock_randint, mock_random, model, mock_storage):
    model.bank = 100
    result, msg = await model.advance(1)
    assert result == "tackled"
    assert "Tackled!" in msg
    assert model.bank == 0
    mock_storage.update_user_score.assert_awaited()


# -------------------------
# TEST: advance — goal reached
# -------------------------
@pytest.mark.asyncio
@patch("random.random", return_value=1.0)  # high roll → avoid tackle
@patch("random.randint", return_value=50)
async def test_advance_goal(mock_randint, mock_random, model, mock_storage):
    model.position = 90
    model.current = 50
    result, msg = await model.advance(1)
    assert result == "banked"
    assert "GOAL" in msg
    mock_storage.update_user_score.assert_awaited()


# -------------------------
# TEST: hold
# -------------------------
@pytest.mark.asyncio
async def test_hold(model, mock_storage):
    model.current = 30
    banked = await model.hold(1)
    assert banked == 30
    assert model.current == 0
    assert model.in_attack
    mock_storage.update_user_score.assert_awaited()



# -------------------------
# TEST: reset_progress
# -------------------------
@pytest.mark.asyncio
async def test_reset_progress(model, mock_storage):
    model.bank = 100
    model.high_score = 200
    await model.reset_progress(1)
    assert model.bank == 0
    assert model.high_score == 0
    mock_storage.update_user_score.assert_awaited()


# -------------------------
# TEST: get_scores
# -------------------------
@pytest.mark.asyncio
async def test_get_scores(model, mock_storage):
    scores = await model.get_scores(2)
    assert isinstance(scores, list)
    assert scores[0]["username"] == "Alice"
    mock_storage.get_scores.assert_awaited_with(2)


# -------------------------
# TEST: cleanup
# -------------------------
@pytest.mark.asyncio
async def test_cleanup(model, mock_storage):
    await model.cleanup()
    mock_storage.close_connection.assert_awaited_once()
