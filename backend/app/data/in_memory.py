import pandas as pd
from typing import List, Dict, Any, Set
from datetime import date
import hashlib
from .base import TenderDataSource

class InMemoryTenderDataSource(TenderDataSource):
    """
    An in-memory implementation of TenderDataSource used strictly for isolated
    batch analysis. It does not write to the database and serves read requests
    using pandas DataFrames constructed from the parsed batch documents.
    """
    def __init__(self, tenders: List[Dict], bids: List[Dict]):
        # tenders shape: list of dicts with tender_id, department, category, region, eligibility_text, estimated_value, award_value, published_date, award_date
        # bids shape: list of dicts with tender_id, vendor_name, bid_amount, is_winner
        self.tenders_df = pd.DataFrame(tenders) if tenders else pd.DataFrame(
            columns=["tender_id", "department", "category", "region", "eligibility_text", "estimated_value", "award_value", "published_date", "award_date"]
        )
        self.bids_df = pd.DataFrame(bids) if bids else pd.DataFrame(
            columns=["tender_id", "vendor_name", "bid_amount", "is_winner"]
        )
        
        if not self.bids_df.empty:
            # Map vendor_name to a dummy integer vendor_id for the interface
            # using a consistent hash
            self.bids_df["vendor_id"] = self.bids_df["vendor_name"].apply(
                lambda name: int(hashlib.sha256(name.encode('utf-8')).hexdigest()[:8], 16)
            )

    def get_department_win_counts(self) -> pd.DataFrame:
        if self.bids_df.empty or self.tenders_df.empty:
            return pd.DataFrame(columns=["department", "vendor_id", "win_count"])
            
        winners = self.bids_df[self.bids_df["is_winner"] == True]
        merged = winners.merge(self.tenders_df, on="tender_id")
        
        counts = merged.groupby(["department", "vendor_id"]).size().reset_index(name="win_count")
        return counts

    def get_category_win_counts(self) -> pd.DataFrame:
        if self.bids_df.empty or self.tenders_df.empty:
            return pd.DataFrame(columns=["category", "vendor_id", "win_count"])
            
        winners = self.bids_df[self.bids_df["is_winner"] == True]
        merged = winners.merge(self.tenders_df, on="tender_id")
        
        counts = merged.groupby(["category", "vendor_id"]).size().reset_index(name="win_count")
        return counts

    def get_single_bidder_tender_ids(self) -> Set:
        if self.bids_df.empty:
            return set()
        # Count distinct vendors per tender
        counts = self.bids_df.groupby("tender_id")["vendor_name"].nunique()
        return set(counts[counts == 1].index)

    def get_eligibility_texts(self) -> pd.DataFrame:
        if self.tenders_df.empty:
            return pd.DataFrame(columns=["tender_id", "category", "eligibility_text"])
        return self.tenders_df[["tender_id", "category", "eligibility_text"]]

    def get_tender_summary(self) -> pd.DataFrame:
        if self.tenders_df.empty or self.bids_df.empty:
            return pd.DataFrame(columns=["tender_id", "department", "category", "winning_vendor"])
            
        winners = self.bids_df[self.bids_df["is_winner"] == True]
        merged = self.tenders_df.merge(winners, on="tender_id", how="left")
        merged["winning_vendor"] = merged["vendor_name"]
        return merged[["tender_id", "department", "category", "winning_vendor"]]

    def get_canonical_categories(self) -> list[str]:
        if self.tenders_df.empty:
            return []
        return self.tenders_df["category"].unique().tolist()

    def get_or_create_department(self, name: str, region: str) -> int:
        raise NotImplementedError("InMemoryTenderDataSource does not support writes. This flow must be strictly isolated.")

    def get_or_create_vendor(self, name: str) -> int:
        raise NotImplementedError("InMemoryTenderDataSource does not support writes. This flow must be strictly isolated.")
    
    def insert_tender(self, department_id: int, category: str, region: str, eligibility_text: str, estimated_value: float, award_value: float, published_date: date, award_date: date) -> int:
        raise NotImplementedError("InMemoryTenderDataSource does not support writes. This flow must be strictly isolated.")

    def insert_bids(self, tender_id: int, bids: List[Dict[str, Any]]) -> None:
        raise NotImplementedError("InMemoryTenderDataSource does not support writes. This flow must be strictly isolated.")
