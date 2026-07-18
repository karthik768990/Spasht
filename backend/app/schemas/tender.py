from pydantic import BaseModel
from typing import Optional

class TenderReportResponse(BaseModel):
    tender_id: int
    department: str
    category: str
    winning_vendor: Optional[str]
    
    # Transparency requirement: scores are strictly separated
    dept_hhi: float
    dept_hhi_label: str
    
    category_hhi: float
    category_hhi_label: str
    
    eligibility_deviation_score: Optional[float]
    
    single_bidder_flag: bool
    pattern_classification: str
