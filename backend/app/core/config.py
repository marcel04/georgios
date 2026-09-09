from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required settings read from FRONTEND_URL and DATABASE_URL.
    frontend_url: str
    database_url: str

    # Look for .env in the working directory (run commands from backend/).
    # Environment variables take precedence over values in this file.
    model_config = SettingsConfigDict(env_file=".env")


# Load and validate settings when this module is first imported.
settings = Settings()
