import datetime
import os
from typing import Annotated
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import sys
import json
from datetime import timedelta
from typing import Optional

import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import create_tables, add_user, add_data, engine, add_log
from src.extract_data import extraire_donnees
from app.auth import auth
from app.auth.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user
from app.auth.models import User
from app.auth.models import Token
from app.helpers.helpers import save_uploaded_file, extract_data_from_file, add_data_to_database, convert_dataframes_to_json
from src.database import get_all_factures, get_facture_by_id, get_all_clients, get_client_by_id, get_all_achats, get_achat_by_id, get_all_produits, get_produit_by_id
from fastapi.middleware.cors import CORSMiddleware
from src.clustering import RFMClustering, KmeansClustering


app = FastAPI()

rfm_model = RFMClustering()
rfm_model.classify()

kmeans_model = KmeansClustering()
kmeans_model.load_model()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/token", summary="Login for access token", response_model=Token, tags=["authentication"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Login for access token.

    Args:
        form_data (Annotated[OAuth2PasswordRequestForm, Depends()]): The form data.

    Returns:
        Token: The access token.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=90)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/", response_model=User, tags=["authentication"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

@app.post("/process", summary="Process uploaded file", tags=["OCR"])
async def create_item(
    file: UploadFile = File(...),
    current_user: bool = Depends(get_current_user)  # Using the dependency
):
    """
    Create item.

    Args:
        file (UploadFile): The uploaded file.
        current_user (bool): The current user.

    Returns:
        JSONResponse: The JSON response.
    """
    try:
        file_location = await save_uploaded_file(file)
        extract_result = extract_data_from_file(file_location)

        add_data_to_database(engine, extract_result)
        data = convert_dataframes_to_json(extract_result)

        if data is None:
            add_log(datetime.datetime.now(), file_location, extract_result["erreur"])
            return JSONResponse(content={"status": "error", "erreur": extract_result["erreur"], "data": None})
        else:
            return JSONResponse(content={"status": "success", "erreur": None, "data": data})

    except HTTPException as http_exception:
        add_log(datetime.datetime.now(), file.filename, http_exception.detail)
        return JSONResponse(content={"status": "error", "erreur": http_exception.detail, "data": None})
    except Exception as e:
        add_log(datetime.datetime.now(), file.filename, str(e))
        return JSONResponse(content={"status": "error", "erreur": str(e), "data": None})

@app.get("/factures", summary="Read all factures", tags=["Database"])
async def read_all_factures():
    """
    Read all factures.
    Returns:
        list: The list of factures.
    """
    factures = get_all_factures()
    return factures

@app.get("/factures/{id_facture}", summary="Read facture by id", tags=["Database"])
async def read_facture(id_facture: str):
    """
    Read facture by id.
    Args:
        id_facture (str): The id of the facture.
    """
    facture_data = get_facture_by_id(id_facture)
    if facture_data is None:
        raise HTTPException(status_code=404, detail="Facture not found")
    return facture_data

@app.get("/clients", summary="Read all clients", tags=["Database"])
async def read_all_clients():
    """
    Read all clients.
    """
    clients = get_all_clients()
    return clients

@app.get("/clients/{id_client}", summary="Read client by id", tags=["Database"])
async def read_client(id_client: str):
    """
    Read client by id.
    Args:
        id_client (str): The id of the client.
    """
    client_data = get_client_by_id(id_client)
    if client_data is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_data

@app.get("/achats", summary="Read all achats", tags=["Database"])
async def read_all_achats():
    """
    Read all achats.
    """
    achats = get_all_achats()
    return achats

@app.get("/achats/{id_produit}/{id_client}/{id_facture}", summary="Read achat by id", tags=["Database"])
async def read_achat(id_produit: str, id_client: str, id_facture: str):
    """
    Read achat by id.
    Args:
        id_produit (str): The id of the produit.
        id_client (str): The id of the client.
        id_facture (str): The id of the facture.
    """
    achat = get_achat_by_id(id_produit, id_client, id_facture)
    if achat is None:
        raise HTTPException(status_code=404, detail="Achat not found")
    return achat

@app.get("/produits", summary="Read all produits", tags=["Database"])
async def read_all_produits():
    """
    Read all produits.
    """
    produits = get_all_produits()
    return produits

@app.get("/produits/{id_produit}", summary="Read produit by id", tags=["Database"])
async def read_produit(id_produit: str):
    """
    Read produit by id.
    Args:
        id_produit (str): The id of the produit.
    """
    produit_data = get_produit_by_id(id_produit)
    if produit_data is None:
        raise HTTPException(status_code=404, detail="Produit not found")
    return produit_data

@app.get("/clustering/rfm", summary="Get RFM clustering", tags=["Clustering"])
async def get_rfm_clustering():
    """
    Get RFM clustering.
    """
    df = rfm_model.df
    clients = {}
    for _, client in df.iterrows():
        clients[client['id_client']] = {
            "total_depense": client['total_depense'] if not pd.isna(client['total_depense']) else None,
            "score_depense": client['score_depense'] if not pd.isna(client['score_depense']) else None,
            "nombre_de_commande": client['nombre_de_commande'] if not pd.isna(client['nombre_de_commande']) else None,
            "score_frequence": client['score_frequence'] if not pd.isna(client['score_frequence']) else None,
            "jours_depuis_derniere_facture": client['jours_depuis_derniere_facture'] if not pd.isna(client['jours_depuis_derniere_facture']) else None,
            "score_recence": client['score_recence'] if not pd.isna(client['score_recence']) else None,
            "segment": client['segment'] if not pd.isna(client['segment']) else None
        }
    clients[client['id_client']] = {k: None if isinstance(v, float) and (v != v) else v for k, v in clients[client['id_client']].items()}
    return clients

@app.get("/clustering/kmeans", summary="Get Kmeans clustering", tags=["Clustering"])
async def get_kmeans_clustering():
    """
    Get Kmeans clustering.
    """
    df = kmeans_model.df
    clients = {}
    for _, client in df.iterrows():
        clients[client['id_client']] = {
            "total_depense": client['total_depense'] if not pd.isna(client['total_depense']) else None,
            "score_depense": client['score_depense'] if not pd.isna(client['score_depense']) else None,
            "nombre_de_commande": client['nombre_de_commande'] if not pd.isna(client['nombre_de_commande']) else None,
            "score_frequence": client['score_frequence'] if not pd.isna(client['score_frequence']) else None,
            "jours_depuis_derniere_facture": client['jours_depuis_derniere_facture'] if not pd.isna(client['jours_depuis_derniere_facture']) else None,
            "score_recence": client['score_recence'] if not pd.isna(client['score_recence']) else None,
            "age": client['age'] if not pd.isna(client['age']) else None,
            "segment": client['cluster'] if not pd.isna(client['cluster']) else None
        }
    clients[client['id_client']] = {k: None if isinstance(v, float) and (v != v) else v for k, v in clients[client['id_client']].items()}
    return clients