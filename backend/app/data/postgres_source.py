"""
PostgresTenderDataSource — real implementation of TenderDataSource.
Aggregation happens in SQL (GROUP BY), not in pandas — only small,
already-aggregated result sets cross into Python.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from typing import List, Dict, Any
from datetime import date

from .base import TenderDataSource


class PostgresTenderDataSource(TenderDataSource):
    def __init__(self, database_url: str, timeout: int = 30):
        self.engine = create_engine(
            database_url,
            connect_args={"connect_timeout": timeout}
        )

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

    # =========================================================================
    # WRITE METHODS
    # =========================================================================

    def get_or_create_department(self, name: str, region: str) -> int:
        query = text("""
            INSERT INTO departments (name, region)
            VALUES (:name, :region)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING department_id;
        """)
        with self.engine.begin() as conn:
            result = conn.execute(query, {"name": name, "region": region})
            return result.scalar()

    def get_or_create_vendor(self, name: str) -> int:
        check_query = text("SELECT vendor_id FROM vendors WHERE name = :name LIMIT 1;")
        insert_query = text("""
            INSERT INTO vendors (name) 
            VALUES (:name) 
            RETURNING vendor_id;
        """)
        with self.engine.begin() as conn:
            existing_id = conn.execute(check_query, {"name": name}).scalar()
            if existing_id:
                return existing_id
            result = conn.execute(insert_query, {"name": name})
            return result.scalar()

    def insert_tender(
        self, department_id: int, category: str, region: str, 
        eligibility_text: str, estimated_value: float, award_value: float, 
        published_date: date, award_date: date
    ) -> int:
        query = text("""
            INSERT INTO tenders 
            (department_id, category, region, eligibility_text, estimated_value, award_value, published_date, award_date)
            VALUES 
            (:dept_id, :category, :region, :eligibility, :est_val, :award_val, :pub_date, :award_date)
            RETURNING tender_id;
        """)
        params = {
            "dept_id": department_id,
            "category": category,
            "region": region,
            "eligibility": eligibility_text,
            "est_val": estimated_value,
            "award_val": award_value,
            "pub_date": published_date,
            "award_date": award_date
        }
        with self.engine.begin() as conn:
            result = conn.execute(query, params)
            return result.scalar()

    def insert_bids(self, tender_id: int, bids: List[Dict[str, Any]]) -> None:
        if not bids:
            return
            
        query = text("""
            INSERT INTO bids (tender_id, vendor_id, bid_amount, is_winner)
            VALUES (:tender_id, :vendor_id, :bid_amount, :is_winner)
            ON CONFLICT (tender_id, vendor_id) DO NOTHING;
        """)
        
        params = [
            {
                "tender_id": tender_id,
                "vendor_id": b["vendor_id"],
                "bid_amount": b["bid_amount"],
                "is_winner": b["is_winner"]
            }
            for b in bids
        ]
        
        with self.engine.begin() as conn:
            conn.execute(query, params)
