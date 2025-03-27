import uvicorn
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.app import app

def run_production_server():
    """Run the API server in production mode"""
    # Import the production config
    import config_prod as config
    
    # Run the server
    uvicorn.run(
        "app.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
        workers=config.WORKERS
    )

if __name__ == "__main__":
    run_production_server()