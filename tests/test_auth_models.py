import pytest
from app.auth.models import UserInDB

def test_user_creation():
    user = UserInDB(username="testuser", hashed_password="hashed_password")
    assert user.username == "testuser"
    assert user.hashed_password == "hashed_password"
    assert user.disabled == None
