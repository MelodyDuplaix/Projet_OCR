from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, status
from fastapi.responses import JSONResponse
from typing import Annotated, Dict, Any, List
from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm
from app.auth.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user
from app.auth.models import Token, User
from app.helpers.helpers import save_uploaded_file, extract_data_from_file, add_data_to_database, convert_dataframes_to_json
from src.database import Facture, Log, SessionLocal, get_all_factures, get_facture_by_id, get_all_clients, get_client_by_id, get_all_achats, get_achat_by_id, get_all_produits, get_produit_by_id
from src.clustering import RFMClustering, KmeansClustering
from app.helpers.monitoring import monitor
import pandas as pd
from sqlalchemy import create_engine
from src.database import engine
import datetime

router = APIRouter()

rfm_model = RFMClustering()
rfm_model.classify()

kmeans_model = KmeansClustering()
kmeans_model.load_model()

@router.post("/token", summary="Login for access token", response_model=Token, tags=["authentication"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    try:
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
    except Exception as e:
        return JSONResponse(content={"status": "error", "erreur": str(e), "data": None})

@router.get("/", response_model=User, tags=["authentication"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    try:
        return current_user
    except Exception as e:
        return JSONResponse(content={"status": "error", "erreur": str(e), "data": None})

@router.post("/process", summary="Process uploaded file", tags=["OCR"])
async def create_item(
    file: UploadFile = File(...),
    current_user: bool = Depends(get_current_user)
):
    """
    Process the uploaded file and extract data.
    """
    try:
        file_location = await save_uploaded_file(file)
        extract_result = extract_data_from_file(file_location)

        # Check if the extraction result contains an error
        if "erreur" in extract_result and extract_result["erreur"]:
            return {"status": "error", "erreur": extract_result["erreur"], "data": None}

        # Add data to the database and convert to JSON
        add_data_to_database(engine, extract_result)
        data = convert_dataframes_to_json(extract_result)

        return {"status": "success", "erreur": None, "data": data}
    except Exception as e:
        # Return a JSON response for unexpected errors
        return {"status": "error", "erreur": str(e), "data": None}

@router.get("/factures", summary="Read all factures", tags=["Database"])
async def read_all_factures():
    try:
        factures = get_all_factures()
        return factures
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/factures/{id_facture}", summary="Read facture by id", tags=["Database"])
async def read_facture(id_facture: str):
    try:
        facture_data = get_facture_by_id(id_facture)
        if facture_data is None:
            raise HTTPException(status_code=404, detail="Facture not found")
        return facture_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients", summary="Read all clients", tags=["Database"])
async def read_all_clients():
    try:
        clients = get_all_clients()
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients/{id_client}", summary="Read client by id", tags=["Database"])
async def read_client(id_client: str):
    try:
        client_data = get_client_by_id(id_client)
        if client_data is None:
            raise HTTPException(status_code=404, detail="Client not found")
        return client_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/achats", summary="Read all achats", tags=["Database"])
async def read_all_achats():
    try:
        achats = get_all_achats()
        return achats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/achats/{id_produit}/{id_client}/{id_facture}", summary="Read achat by id", tags=["Database"])
async def read_achat(id_produit: str, id_client: str, id_facture: str):
    try:
        achat = get_achat_by_id(id_produit, id_client, id_facture)
        if achat is None:
            raise HTTPException(status_code=404, detail="Achat not found")
        return achat
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/produits", summary="Read all produits", tags=["Database"])
async def read_all_produits():
    try:
        produits = get_all_produits()
        return produits
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/produits/{id_produit}", summary="Read produit by id", tags=["Database"])
async def read_produit(id_produit: str):
    try:
        produit_data = get_produit_by_id(id_produit)
        if produit_data is None:
            raise HTTPException(status_code=404, detail="Produit not found")
        return produit_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clustering/rfm", summary="Get RFM clustering", tags=["Clustering"])
async def get_rfm_clustering():
    try:
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
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clustering/kmeans", summary="Get Kmeans clustering", tags=["Clustering"])
async def get_kmeans_clustering():
    try:
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
        return clients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/OCR", summary="API metrics", tags=["Monitoring"])
async def metrics_ocr():
    """
    Returns monitoring metrics for the API.
    Includes:
    - Total requests
    - Error rate
    - List of errors
    """
    try:
        with SessionLocal() as session:
            total_requests = session.query(Facture.id_facture).outerjoin(
                Log, Log.fichier == Facture.id_facture
            ).count()
            error_rate = session.query(Log).count() / total_requests
            error_list = [error[0] for error in session.query(Log.erreur).all()]
            
        return {
            "total_requests": total_requests,
            "error_rate": error_rate,
            "error_list": error_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/metrics",
    summary="API metrics",
    description="Returns monitoring metrics for the API",
    tags=["Monitoring"],
    response_model=Dict[str, Any]
)
async def metrics():
    """
    Returns monitoring metrics for the API.
    
    Includes:
    - Uptime
    - Total requests
    - Error rate
    - Endpoint-specific metrics
    """
    return monitor.get_statistics()

@router.get(
    "/metrics/requests",
    summary="Recent requests",
    description="Returns information about recent API requests",
    tags=["Monitoring"],
    response_model=List[Dict[str, Any]]
)
async def recent_requests(limit: int = Query(10, ge=1, le=100)):
    """Returns information about the most recent API requests"""
    return monitor.get_recent_requests(limit=limit)

@router.get(
    "/metrics/errors",
    summary="Recent errors",
    description="Returns information about recent API errors",
    tags=["Monitoring"],
    response_model=List[Dict[str, Any]]
)
async def recent_errors(limit: int = Query(10, ge=1, le=100)):
    """Returns information about the most recent API errors"""
    return monitor.get_recent_errors(limit=limit)