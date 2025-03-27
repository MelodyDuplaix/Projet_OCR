import pytest
from app.helpers import helpers
import os
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_save_uploaded_file(tmp_path):
    file = MagicMock()
    file.filename = "test.txt"
    file.file.read.return_value = b"test content"  # Correctly mock file.read() to return bytes
    file_location = await helpers.save_uploaded_file(file)
    assert os.path.exists(file_location)
    assert os.path.basename(file_location) == "test.txt"

@pytest.mark.asyncio
async def test_save_uploaded_file_error(mocker):
    file = MagicMock()
    file.filename = "test.txt"
    file.file.read.side_effect = IOError("File read error")  # Simulate file read error

    with pytest.raises(Exception, match="Failed to save file: File read error"):
        await helpers.save_uploaded_file(file)

def test_extract_data_from_file(mocker):
    mock_file_location = "temp/test.txt"
    mock_extract_result = {"status": "success", "data": "mocked_data"}
    mocker.patch("app.helpers.helpers.extraire_donnees", return_value=mock_extract_result)

    result = helpers.extract_data_from_file(mock_file_location)
    assert result == mock_extract_result

def test_extract_data_from_file_error(mocker):
    mock_file_location = "temp/test.txt"
    mocker.patch("app.helpers.helpers.extraire_donnees", side_effect=Exception("Extraction error"))

    with pytest.raises(Exception, match="Extraction error"):
        helpers.extract_data_from_file(mock_file_location)

def test_add_data_to_database(mocker):
    mock_engine = MagicMock()
    mock_extract_result = {
        "status": "success",
        "data": ["df_client", "df_facture", "df_produit", "df_achat"],
    }
    mocker.patch("app.helpers.helpers.add_data")

    helpers.add_data_to_database(mock_engine, mock_extract_result)

    helpers.add_data.assert_any_call(mock_engine, "client", "df_client")
    helpers.add_data.assert_any_call(mock_engine, "facture", "df_facture")
    helpers.add_data.assert_any_call(mock_engine, "produit", "df_produit")
    helpers.add_data.assert_any_call(mock_engine, "achat", "df_achat")

def test_add_data_to_database_error(mocker):
    mock_engine = MagicMock()
    mock_extract_result = {"status": "error", "erreur": "Mocked error"}
    
    with pytest.raises(Exception, match="Mocked error"):
        helpers.add_data_to_database(mock_engine, mock_extract_result)

def test_convert_dataframes_to_json(mocker):
    mock_df_client = MagicMock()
    mock_df_facture = MagicMock()
    mock_df_produit = MagicMock()
    mock_df_achat = MagicMock()

    mock_df_client.to_json.return_value = '{"client": "mock_client"}'
    mock_df_facture.to_json.return_value = '{"facture": "mock_facture"}'
    mock_df_produit.to_json.return_value = '{"produit": "mock_produit"}'
    mock_df_achat.to_json.return_value = '{"achat": "mock_achat"}'

    mock_extract_result = {
        "status": "success",
        "data": [mock_df_client, mock_df_facture, mock_df_produit, mock_df_achat],
    }

    result = helpers.convert_dataframes_to_json(mock_extract_result)

    assert result == {
        "client": {"client": "mock_client"},
        "facture": {"facture": "mock_facture"},
        "produit": {"produit": "mock_produit"},
        "achat": {"achat": "mock_achat"},
    }

def test_convert_dataframes_to_json_error():
    mock_extract_result = {"status": "error", "erreur": "Mocked error"}
    result = helpers.convert_dataframes_to_json(mock_extract_result)
    assert result is None
