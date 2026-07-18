from .data.postgres_source import PostgresTenderDataSource
from .config import settings

def get_data_source() -> PostgresTenderDataSource:
    return PostgresTenderDataSource(settings.DATABASE_URL, timeout=settings.DB_TIMEOUT)
