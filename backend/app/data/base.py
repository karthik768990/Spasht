"""
TenderDataSource — the pluggability boundary. Anything the scoring/service
layer needs from storage, as an abstract contract. Implementations (Postgres,
synthetic, future sources) live alongside this file; scoring.py only ever
consumes the plain pandas structures these methods return.
"""

from abc import ABC, abstractmethod
import pandas as pd
from  typing import List,Any,Dict
from datetime import date

class TenderDataSource(ABC):

    @abstractmethod
    def get_department_win_counts(self) -> pd.DataFrame:
        """Columns: department, vendor_id, win_count."""
        ...

    @abstractmethod
    def get_category_win_counts(self) -> pd.DataFrame:
        """Columns: category, vendor_id, win_count."""
        ...

    @abstractmethod
    def get_single_bidder_tender_ids(self) -> set:
        """Set of tender_ids that received exactly one distinct bidder."""
        ...

    @abstractmethod
    def get_eligibility_texts(self) -> pd.DataFrame:
        """Columns: tender_id, category, eligibility_text."""
        ...

    @abstractmethod
    def get_tender_summary(self) -> pd.DataFrame:
        """Columns: tender_id, department, category, winning_vendor."""
        ...

    @abstractmethod
    def get_canonical_categories(self) -> list[str]:
        """Distinct category values currently known to the system — used
        by the category matcher (Job B) to decide whether a newly parsed
        document's category is an existing one or genuinely new."""
        ...

    # =========================================================================
    # WRITE METHODS
    # =========================================================================

    @abstractmethod
    def get_or_create_department(self, name: str, region: str) -> int:
        """Returns the department_id, creating it if it doesn't exist."""
        pass

    @abstractmethod
    def get_or_create_vendor(self, name: str) -> int:
        """Returns the vendor_id, creating it if it doesn't exist."""
        pass
    
    @abstractmethod
    def insert_tender(self, department_id: int, category: str, region: str, eligibility_text: str, estimated_value: float, award_value: float, published_date: date, award_date: date) -> int:
        """Inserts a new tender and returns its tender_id."""
        pass

    @abstractmethod
    def insert_bids(self, tender_id: int, bids: List[Dict[str, Any]]) -> None:
        """
        Inserts bids for a given tender. 
        `bids` format: [{'vendor_id': int, 'bid_amount': float, 'is_winner': bool}]
        """
        pass