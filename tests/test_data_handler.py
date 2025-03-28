import pytest
from frontend.helpers import data_handler
import requests
from unittest.mock import MagicMock

def test_get_data_for_facture(mocker):
    mock_headers = {"Authorization": "Bearer test_token"}
    mock_id_facture = "test_id"
    mock_fastapi_url = "http://test_url"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "facture": {"date_facturation": "2025-03-27T10:00:00"},
        "client": {"birthdate": "1990-01-01T00:00:00"},
        "products": [
            {
                "product": {
                    "id_produit": 1,
                    "nom": "Product A",
                    "prix": 100.0,
                },
                "quantity": 2,
            }
        ],
    }

    mocker.patch("requests.get", return_value=mock_response)

    facture, client, products = data_handler.get_data_for_facture(
        mock_headers, mock_id_facture, mock_fastapi_url
    )

    assert facture == {"date_facturation": "2025-03-27"}
    assert client == {"birthdate": "1990-01-01"}
    assert products == [
        {
            "id_produit": 1,
            "nom": "Product A",
            "prix": 100.0,
            "quantite": 2,
        }
    ]

def test_get_data_for_facture_unauthorized(mocker):
    mock_headers = {"Authorization": "Bearer test_token"}
    mock_id_facture = "test_id"
    mock_fastapi_url = "http://test_url"

    mock_response = MagicMock()
    mock_response.status_code = 401
    mocker.patch("requests.get", return_value=mock_response)

    with pytest.raises(Exception, match="Unauthorized"):
        data_handler.get_data_for_facture(mock_headers, mock_id_facture, mock_fastapi_url)

def test_get_data_for_facture_invalid_response(mocker):
    mock_headers = {"Authorization": "Bearer test_token"}
    mock_id_facture = "test_id"
    mock_fastapi_url = "http://test_url"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"invalid_key": "invalid_value"}  # Missing expected keys
    mocker.patch("requests.get", return_value=mock_response)

    with pytest.raises(KeyError):
        data_handler.get_data_for_facture(mock_headers, mock_id_facture, mock_fastapi_url)

def test_get_data_for_facture_partial_data(mocker):
    mock_headers = {"Authorization": "Bearer test_token"}
    mock_id_facture = "test_id"
    mock_fastapi_url = "http://test_url"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "facture": {"date_facturation": "2025-03-27T10:00:00"},
        # Missing "client" and "products"
    }
    mocker.patch("requests.get", return_value=mock_response)

    with pytest.raises(KeyError):
        data_handler.get_data_for_facture(mock_headers, mock_id_facture, mock_fastapi_url)
