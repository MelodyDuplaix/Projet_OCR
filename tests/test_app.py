import pytest
from fastapi.testclient import TestClient
from app.app import app

client = TestClient(app)

def test_upload_no_token():
    response = client.post("/upload")
    assert response.status_code in [307, 404]  # Redirect to login or route not found
    if response.status_code == 307:
        assert "login" in response.headers.get("location", "")

def test_dashboard_no_token():
    response = client.get("/dashboard")
    assert response.status_code in [307, 404]  # Redirect to login or route not found
    if response.status_code == 307:
        assert "login" in response.headers.get("location", "")
