from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    frontend_url: str
    database_url: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
