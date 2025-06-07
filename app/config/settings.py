from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    ESTATED_API_KEY: str = "YOUR_ESTATED_API_KEY_HERE"
    ZWSID: str = "YOUR_ZWSID_HERE"
    GOOGLE_API_KEY: str = "YOUR_GOOGLE_API_KEY_HERE"
    RENTCAST_API_KEY: str = "YOUR_RENTCAST_API_KEY_HERE"

    # Optional: If you use a .env file for local development
    # model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# To make settings available application-wide and cache them
@lru_cache()
def get_settings() -> Settings:
    return Settings()
