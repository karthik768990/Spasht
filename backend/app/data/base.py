"""
TenderDataSource — the pluggability boundary. Anything the scoring/service
layer needs from storage, as an abstract contract. Implementations (Postgres,
synthetic, future sources) live alongside this file; scoring.py only ever
consumes the plain pandas structures these methods return.
"""

from abc import ABC, abstractmethod
import pandas as pd


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
