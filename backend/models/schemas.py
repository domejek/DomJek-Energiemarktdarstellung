from pydantic import BaseModel
from typing import Optional, List


class DateRange(BaseModel):
    start: str
    end: str
    source: str = "demo"


class PrlRecord(BaseModel):
    timestamp: str
    deutschland_positiv_mw: float
    deutschland_negativ_mw: float
    _50hertz_mw: Optional[float] = None
    amprion_mw: Optional[float] = None
    tennet_mw: Optional[float] = None
    transnetbw_mw: Optional[float] = None


class AffrRecord(BaseModel):
    timestamp: str
    deutschland_positiv_mw: float
    deutschland_negativ_mw: float
    _50hertz_positiv_mw: Optional[float] = None
    amprion_positiv_mw: Optional[float] = None
    tennet_positiv_mw: Optional[float] = None
    transnetbw_positiv_mw: Optional[float] = None


class PrlResponse(BaseModel):
    data: List[PrlRecord]
    metadata: dict


class AffrResponse(BaseModel):
    data: List[AffrRecord]
    metadata: dict


class StatisticsResponse(BaseModel):
    prl: dict
    affr: dict


class DailySummaryResponse(BaseModel):
    prl_daily: List[dict]
    affr_daily: List[dict]


class UploadResponse(BaseModel):
    success: bool
    rows: int
    columns: List[str]
    preview: List[dict]
