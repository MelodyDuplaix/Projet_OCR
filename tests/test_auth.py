import pytest
from app.auth import auth

def test_get_password_hash():
    password = "test_password"
    hashed_password = auth.get_password_hash(password)
    assert hashed_password != password
    assert hashed_password.startswith("$2b$")

def test_verify_password():
    plain_password = "test_password"
    hashed_password = auth.get_password_hash(plain_password)
    assert auth.verify_password(plain_password, hashed_password) == True
    assert auth.verify_password("wrong_password", hashed_password) == False

def test_create_access_token():
    data = {"sub": "test_user"}
    token = auth.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0
