from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    DB_TIMEOUT: int = 30  # connection timeout

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
