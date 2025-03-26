import datetime
import json
import os
import time
from typing import Annotated, Any, Dict
from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
import sys
from datetime import timedelta
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import engine, add_log, Log, Facture
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from app.auth.auth import authenticate_user, create_access_token, get_current_active_user, get_current_user
from app.auth.models import User
from app.auth.models import Token
from app.helpers.helpers import save_uploaded_file, extract_data_from_file, add_data_to_database, convert_dataframes_to_json
from src.database import get_all_factures, get_facture_by_id, get_all_clients, get_client_by_id, get_all_achats, get_achat_by_id, get_all_produits, get_produit_by_id
from fastapi.middleware.cors import CORSMiddleware
from src.clustering import RFMClustering, KmeansClustering
from app.helpers.monitoring import monitor
from app.endpoints import router as api_router

 
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

app.include_router(api_router)  # Include the router

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Record request for monitoring"""
    start_time = time.time()
    method = request.method
    path = request.url.path

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Access the response content
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        async def body_iterator():
            yield response_body
        response.body_iterator = body_iterator()
        
        try:
            response_data = response_body.decode("utf-8")
            json_data = json.loads(response_data)
            if json_data.get("status") == "error" and json_data.get("erreur") != "" and json_data.get("erreur") is not None:
                monitor.record_request(
                    method=method,
                    path=path,
                    status_code=400,
                    duration=duration,
                    error=json_data.get("erreur")
                )
                return JSONResponse(content=json_data, status_code=response.status_code)
        except Exception:
            pass

        # Record the request
        monitor.record_request(
            method=method,
            path=path,
            status_code=response.status_code,
            duration=duration
        )
        return response
    except Exception as e:
        duration = time.time() - start_time
        monitor.record_request(
            method=method,
            path=path,
            status_code=500,
            duration=duration,
            error=str(e)
        )
        return JSONResponse(
            content={"status": "error", "erreur": str(e), "data": None},
            status_code=500
        )


