import logging
import logging.config
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import assessment, candidate, analytics
from config import settings # Import settings to ensure config is loaded
from services.openrouter_service import shutdown_http_client # Import shutdown function
import uvicorn

# --- Logging Configuration ---
# Basic config, consider using a dictConfig for more complex setups (e.g., file rotation)
logging.basicConfig(
    level=logging.INFO, # Set root logger level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Optionally decrease level for specific noisy loggers like uvicorn access
# logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- Lifespan Management (for setup/teardown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Application startup...")
    logger.info(f"Using OpenRouter Analysis Model: {settings.OPENROUTER_MODEL_ANALYSIS}")
    # Initialize shared resources if needed (like DB connections, HTTP client is created on demand)
    yield
    # Shutdown actions
    logger.info("Application shutdown...")
    await shutdown_http_client() # Close the shared HTTP client gracefully


# --- FastAPI App ---
app = FastAPI(
    title="AI Personality Assessment API",
    description="API for conducting AI-powered personality assessments based on behavioral responses.",
    version="0.2.0", # Incremented version
    lifespan=lifespan # Use lifespan context manager
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assessment.router)
app.include_router(candidate.router)
app.include_router(analytics.router)

@app.get("/", tags=["Root"])
async def read_root():
    """ Basic endpoint to check if the API is running. """
    return {"message": "Welcome to the AI Personality Assessment API!"}

# Example of how to run directly (for development)
if __name__ == "__main__":
    logger.info("Starting API server in development mode...")
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)