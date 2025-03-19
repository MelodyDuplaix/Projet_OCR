from fastapi.testclient import TestClient
from app.app import app
import os
from fastapi import status

client = TestClient(app)

def test_process():
    token = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"},
    ).json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    
    file_path = os.path.abspath("temp/FAC2_OK.png")
    with open(file_path, "rb") as file:  # Utilisation d'un gestionnaire de contexte
        response = client.post(
            "/process",
            files={"file": ("FAC2_OK.png", file)},
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["erreur"] is None
    assert response.json()["status"] == "success"
    assert response.json()["data"] is not None
