from fastapi import APIRouter, Depends
from typing import List
from ..schemas.tender import TenderReportResponse
from ..deps import get_data_source
from ..services.scoring_service import build_report

router = APIRouter()

@router.get("/", response_model=List[TenderReportResponse])
def get_tenders(source = Depends(get_data_source)):
    report_df = build_report(source)
    # Convert DataFrame to list of dicts matching the Pydantic schema
    records = report_df.to_dict("records")
    return records
