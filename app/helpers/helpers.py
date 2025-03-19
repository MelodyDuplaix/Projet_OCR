import os
from typing import Annotated
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sys
import sys
import os
import json
from datetime import timedelta
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import create_tables, add_user, add_data, engine, add_log
from src.extract_data import extraire_donnees
from app.auth import auth
from app.auth.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user
from app.auth.models import User
from app.auth.models import Token

async def save_uploaded_file(file: UploadFile) -> str:
    """Saves the uploaded file to a temporary location."""
    os.makedirs("temp", exist_ok=True)
    file_location = f"temp/{file.filename}"
    try:
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        print(f"File saved at {file_location}")
        return file_location
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

def extract_data_from_file(file_location: str) -> dict:
    """Extracts data from the specified file using the extraire_donnees function."""
    extract = extraire_donnees(file_location)
    return extract

def add_data_to_database(engine, extract_result: dict):
    """Adds the extracted data to the database."""
    if extract_result["status"] == "success":
        df_client, df_facture, df_produit, df_achat = extract_result["data"]
        add_data(engine, "client", df_client)
        add_data(engine, "facture", df_facture)
        add_data(engine, "produit", df_produit)
        add_data(engine, "achat", df_achat)
    else:
        raise HTTPException(status_code=400, detail=extract_result["erreur"])

def convert_dataframes_to_json(extract_result: dict) -> Optional[dict]:
    """Converts the extracted dataframes to JSON format."""
    if extract_result["status"] == "success":
        df_client, df_facture, df_produit, df_achat = extract_result["data"]
        df_client = df_client.to_json(orient="records", date_format="iso")
        df_facture = df_facture.to_json(orient="records", date_format="iso")
        df_produit = df_produit.to_json(orient="records", date_format="iso")
        df_achat = df_achat.to_json(orient="records", date_format="iso")
        data = {
            "client": json.loads(df_client),
            "facture": json.loads(df_facture),
            "produit": json.loads(df_produit),
            "achat": json.loads(df_achat)
        }
        return data
    else:
        return None
