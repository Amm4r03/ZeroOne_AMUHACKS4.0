import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(PROJECT_ROOT, 'config', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOGS_DIR, 'api.log'))
    ]
)

logger = logging.getLogger("edu_video_api")

# Initialize FastAPI app
app = FastAPI(
    title="Educational Video Generator API",
    description="API for generating educational videos from topics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include API router
# Adjust import path based on file location
from .api.router import router
app.include_router(router)

# Exception handler
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred", "details": str(exc)}
    )

# Startup events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Educational Video Generator API")
    # Ensure required directories exist (moved log dir creation earlier)

# Shutdown events
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Educational Video Generator API")


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 4567))
    reload_flag = os.getenv("DEBUG", "False").lower() == "true"
    workers_count = int(os.getenv("API_WORKERS", 1))
    
    logger.info(f"Starting server on port {port} with reload={reload_flag} and workers={workers_count}")
    
    # Use the module path for uvicorn when running directly
    uvicorn.run(
        "edu_video_generator.src.api_server:app",
        host="0.0.0.0",
        port=port,
        reload=reload_flag,
        workers=workers_count
    )
