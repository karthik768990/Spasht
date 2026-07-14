"""
PostgresTenderDataSource — real implementation of TenderDataSource.
Aggregation happens in SQL (GROUP BY), not in pandas — only small,
already-aggregated result sets cross into Python.
"""

import pandas as pd
from sqlalchemy import create_engine

from .base import TenderDataSource


class PostgresTenderDataSource(TenderDataSource):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)

    def get_department_win_counts(self) -> pd.DataFrame:
        query = """
            SELECT d.name AS department, b.vendor_id, COUNT(*) AS win_count
            FROM bids b
            JOIN tenders t ON t.tender_id = b.tender_id
            JOIN departments d ON d.department_id = t.department_id
            WHERE b.is_winner = TRUE
            GROUP BY d.name, b.vendor_id
        """
        with self.engine.connect() as conn:
            return pd.read_sql(query, conn)

    def get_category_win_counts(self) -> pd.DataFrame:
        query = """
            SELECT t.category, b.vendor_id, COUNT(*) AS win_count
            FROM bids b
            JOIN tenders t ON t.tender_id = b.tender_id
            WHERE b.is_winner = TRUE
            GROUP BY t.category, b.vendor_id
        """
        with self.engine.connect() as conn:
            return pd.read_sql(query, conn)

    def get_single_bidder_tender_ids(self) -> set:
        query = """
            SELECT tender_id
            FROM bids
            GROUP BY tender_id
            HAVING COUNT(DISTINCT vendor_id) = 1
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return set(df["tender_id"])

    def get_eligibility_texts(self) -> pd.DataFrame:
        query = "SELECT tender_id, category, eligibility_text FROM tenders"
        with self.engine.connect() as conn:
            return pd.read_sql(query, conn)

    def get_tender_summary(self) -> pd.DataFrame:
        query = """
            SELECT
                t.tender_id,
                d.name AS department,
                t.category,
                v.name AS winning_vendor
            FROM tenders t
            JOIN departments d ON d.department_id = t.department_id
            LEFT JOIN bids b ON b.tender_id = t.tender_id AND b.is_winner = TRUE
            LEFT JOIN vendors v ON v.vendor_id = b.vendor_id
        """
        with self.engine.connect() as conn:
            return pd.read_sql(query, conn)

    def get_canonical_categories(self) -> list[str]:
        query = "SELECT DISTINCT category FROM tenders"
        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df["category"].tolist()
