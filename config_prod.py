# config.py
import os
from pathlib import Path
# API configuration
API_TITLE = "Invoices Analysis API"
API_DESCRIPTION = """
    This API provides functionalities for analyzing facture data, including OCR processing,
    database operations, clustering, and monitoring.
    
    ## Features
    
    * Process uploaded facture files and extract data using OCR
    * Store and retrieve facture, client, achat, and produit data from the database
    * Perform RFM and K-means clustering for customer segmentation
    * Monitor API metrics and track recent requests and errors
    
    ## Usage
    
    1. Use the `/process` endpoint to upload and process facture files
    2. Use the `/factures`, `/clients`, `/achats`, and `/produits` endpoints to retrieve data from the database
    3. Use the `/clustering/rfm` and `/clustering/kmeans` endpoints to get clustering data
    4. Use the `/metrics` endpoints to monitor API performance
    
    The API is built with FastAPI and uses various libraries for OCR,
    database management, clustering, and monitoring.
    """


# Server configuration
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))
RELOAD = False
WORKERS = int(os.getenv("WORKER", 1))

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
