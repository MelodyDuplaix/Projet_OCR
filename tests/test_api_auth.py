import pytest
from app.auth import auth
from src.database import User
from datetime import timedelta
# Mock the database and dependencies for testing get_user, authenticate_user, get_current_user, and get_current_active_user
from unittest.mock import MagicMock
import asyncio
from fastapi import HTTPException, status
import jwt

def test_verify_password():
    plain_password = "test_password"
    hashed_password = auth.get_password_hash(plain_password)
    assert auth.verify_password(plain_password, hashed_password) == True
    assert auth.verify_password("wrong_password", hashed_password) == False

def test_get_password_hash():
    password = "test_password"
    hashed_password = auth.get_password_hash(password)
    assert hashed_password != password
    assert hashed_password.startswith("$2b$")

def test_create_access_token():
    data = {"sub": "test_user"}
    token = auth.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

    expires_delta = timedelta(minutes=5)
    token = auth.create_access_token(data, expires_delta)
    assert isinstance(token, str)
    assert len(token) > 0

def test_get_user():
    # Mock the database session and user object
    mock_db = MagicMock()
    mock_user = User(username="testuser")  # Create a User object
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    auth.SessionLocal = MagicMock(return_value=mock_db)

    user = auth.get_user("testuser")
    assert user is not None
    if user is not None:
        assert user.username == "testuser"
    mock_db.close.assert_called_once()

def test_get_user_not_found():
    # Mock the database session to return None for the user
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    auth.SessionLocal = MagicMock(return_value=mock_db)

    user = auth.get_user("testuser")
    assert user is None
    mock_db.close.assert_called_once()

def test_authenticate_user():
    # Mock the get_user function and password verification
    auth.get_user = MagicMock()
    mock_user = User(username="testuser", hashed_password="hashed_password")
    auth.get_user.return_value = mock_user
    auth.verify_password = MagicMock(return_value=True)

    user = auth.authenticate_user("testuser", "password")
    assert user is not False
    auth.get_user.assert_called_once_with("testuser")
    auth.verify_password.assert_called_once_with("password", "hashed_password")

def test_authenticate_user_invalid_password():
    # Mock the get_user function and password verification
    auth.get_user = MagicMock()
    mock_user = User(username="testuser", hashed_password="hashed_password")
    auth.get_user.return_value = mock_user
    auth.verify_password = MagicMock(return_value=False)

    user = auth.authenticate_user("testuser", "password")
    assert user is False
    auth.get_user.assert_called_once_with("testuser")
    auth.verify_password.assert_called_once_with("password", "hashed_password")

def test_authenticate_user_user_not_found():
    # Mock the get_user function to return None
    auth.get_user = MagicMock(return_value=None)

    user = auth.authenticate_user("testuser", "password")
    assert user is False
    auth.get_user.assert_called_once_with("testuser")

@pytest.mark.asyncio
async def test_get_current_user():
    jwt.decode = MagicMock(return_value={"sub": "testuser"})
    mock_db = MagicMock()
    mock_user = User(username="testuser")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    auth.SessionLocal = MagicMock(return_value=mock_db)

    user = await auth.get_current_user("test_token")
    assert user is not None
    mock_db.close.assert_called_once()

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwt.decode = MagicMock(side_effect=credentials_exception)
    with pytest.raises(HTTPException) as excinfo:
        await auth.get_current_user("test_token")
    assert excinfo.value is credentials_exception

@pytest.mark.asyncio
async def test_get_current_active_user():
    mock_user = MagicMock(username="testuser", disabled=False)
    user = await auth.get_current_active_user(mock_user)
    assert user is not None
    if user is not None:
        assert user.username == "testuser"

@pytest.mark.asyncio
async def test_get_current_active_user_inactive():
    mock_user = MagicMock(username="testuser", disabled=True)
    with pytest.raises(HTTPException) as excinfo:
        await auth.get_current_active_user(mock_user)
    assert excinfo.value.status_code == 400
    assert "Inactive user" in excinfo.value.detail
