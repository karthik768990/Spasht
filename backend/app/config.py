from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DB_TIMEOUT: int = 30  # connection timeout

    class Config:
        env_file = ".env"

settings = Settings()
