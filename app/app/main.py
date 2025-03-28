import json
import os
import time
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app.app.config as config
from app.app.utils.database import engine
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from fastapi.middleware.cors import CORSMiddleware
from app.app.utils.clustering import RFMClustering, KmeansClustering
from app.app.utils.monitoring import monitor
from app.app.routers.endpoints import router as api_router
 
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Endpoints for user authentication",
        },
        {
            "name": "OCR",
            "description": "Endpoints for OCR processing",
        },
        {
            "name": "Database",
            "description": "Endpoints for database operations",
        },
        {
            "name": "Clustering",
            "description": "Endpoints for clustering operations",
        },
        {
            "name": "Monitoring",
            "description": "Endpoints for monitoring API metrics",
        },
    ]
)


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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.app.main:app", 
        host=config.HOST, 
        port=config.PORT, 
        reload=config.RELOAD
    )
