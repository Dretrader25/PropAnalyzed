from fastapi import FastAPI
from .config.settings import get_settings
from .utils.logging_utils import setup_logging # New import

# Call setup_logging before creating the FastAPI app or early in startup
setup_logging() # Default level is INFO

app = FastAPI(title="Property Lead Enrichment API")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Placeholder for the main endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Property Lead Enrichment API. Use /docs for API documentation."}

@app.get("/show-settings-test") # Temporary endpoint for testing
async def show_settings():
    settings = get_settings()
    # Never expose all settings like this in production! This is just for setup verification.
    return {
        "estated_key_set": bool(settings.ESTATED_API_KEY) and settings.ESTATED_API_KEY != "YOUR_ESTATED_API_KEY_HERE",
        "google_key_set": bool(settings.GOOGLE_API_KEY) and settings.GOOGLE_API_KEY != "YOUR_GOOGLE_API_KEY_HERE",
        "rentcast_key_set": bool(settings.RENTCAST_API_KEY) and settings.RENTCAST_API_KEY != "YOUR_RENTCAST_API_KEY_HERE",
        "zwsid_set": bool(settings.ZWSID) and settings.ZWSID != "YOUR_ZWSID_HERE",
    }
