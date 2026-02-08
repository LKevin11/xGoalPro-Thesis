import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
import secrets
from unittest.mock import AsyncMock
from Model.Auth import AuthModel

# -------------------------
# FIXTURES
# -------------------------
@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.user_exists.return_value = False
    storage.get_user.return_value = None
    storage.create_user.return_value = None
    return storage

@pytest.fixture
def auth_model(mock_storage):
    return AuthModel(mock_storage)

# -------------------------
# REGISTER TESTS
# -------------------------

@pytest.mark.asyncio
async def test_register_success(auth_model, mock_storage):
    username = "TestUser"
    email = "test@example.com"
    password = "StrongP@ss1"
    confirm_password = "StrongP@ss1"

    ok, data = await auth_model.register(username, email, password, confirm_password)

    assert ok
    assert data[0] == username
    mock_storage.create_user.assert_awaited_once()

@pytest.mark.asyncio
async def test_register_existing_username(auth_model, mock_storage):
    mock_storage.user_exists.return_value = True

    ok, errors = await auth_model.register("TestUser", "test@example.com", "StrongP@ss1", "StrongP@ss1")

    assert not ok
    assert "Username already exists" in errors

@pytest.mark.asyncio
async def test_register_invalid_username_email_password(auth_model):
    username = "ab"  # too short
    email = "invalid_email"
    password = "weak"
    confirm_password = "weak2"

    ok, errors = await auth_model.register(username, email, password, confirm_password)

    assert not ok
    # Username errors
    assert any("Username must" in e for e in errors)
    # Email error
    assert "Email is not valid." in errors
    # Password errors
    assert any("Password must" in e for e in errors)
    # Password mismatch
    assert "Passwords do not match." in errors

@pytest.mark.asyncio
async def test_register_storage_exception(auth_model, mock_storage):
    mock_storage.create_user.side_effect = Exception("DB fail")
    username = "User1"
    email = "user1@example.com"
    password = "StrongP@ss1"

    ok, errors = await auth_model.register(username, email, password, password)
    assert not ok
    assert "Registration failed: DB fail" in errors[0]

# -------------------------
# LOGIN TESTS
# -------------------------

@pytest.mark.asyncio
async def test_login_success(auth_model, mock_storage):
    username = "TestUser"
    password = "StrongP@ss1"
    salt = "123abc"
    hashed_password = auth_model._hash_password(password, salt)

    mock_storage.get_user.return_value = {
        "id": 1,
        "username": username,
        "password_salt": salt,
        "password_hash": hashed_password
    }

    ok, data = await auth_model.login(username, password)
    assert ok
    assert data[0] == username
    assert data[1] == 1

@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_model, mock_storage):
    username = "TestUser"
    password = "WrongPass"
    salt = "123abc"
    hashed_password = auth_model._hash_password("StrongP@ss1", salt)

    mock_storage.get_user.return_value = {
        "id": 1,
        "username": username,
        "password_salt": salt,
        "password_hash": hashed_password
    }

    ok, errors = await auth_model.login(username, password)
    assert not ok
    assert "Invalid credentials" in errors

@pytest.mark.asyncio
async def test_login_nonexistent_user(auth_model, mock_storage):
    mock_storage.get_user.return_value = None

    ok, errors = await auth_model.login("UnknownUser", "AnyPass")
    assert not ok
    assert "User does not exist!" in errors

@pytest.mark.asyncio
async def test_login_storage_exception(auth_model, mock_storage):
    mock_storage.get_user.side_effect = Exception("DB fail")

    ok, errors = await auth_model.login("TestUser", "pass")
    assert not ok
    assert "Login failed: DB fail" in errors[0]

# -------------------------
# INTERNAL METHOD TESTS
# -------------------------

def test_generate_salt(auth_model):
    salt1 = auth_model._generate_salt()
    salt2 = auth_model._generate_salt()
    assert isinstance(salt1, str)
    assert len(salt1) == auth_model._AuthModel__salt_length * 2  # hex representation
    assert salt1 != salt2  # should be random

def test_hash_password(auth_model):
    password = "StrongP@ss1"
    salt = "abcdef"
    hash1 = auth_model._hash_password(password, salt)
    hash2 = auth_model._hash_password(password, salt)
    # same inputs -> same output
    assert hash1 == hash2
    # different password -> different output
    hash3 = auth_model._hash_password("OtherPass", salt)
    assert hash1 != hash3
