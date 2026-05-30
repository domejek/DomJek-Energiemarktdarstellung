from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from datetime import datetime, timedelta

from backend.models.schemas import (
    PrlResponse,
    AffrResponse,
    StatisticsResponse,
    DailySummaryResponse,
    UploadResponse,
)
from backend.services.energy_service import (
    get_prl_data,
    get_affr_data,
    get_statistics,
    get_daily_summary,
    parse_csv_to_preview,
)

router = APIRouter()


@router.get("/prl", response_model=PrlResponse)
async def prl(
    start: str = Query(default=None),
    end: str = Query(default=None),
    source: str = Query(default="demo"),
):
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")

    data, metadata = get_prl_data(start, end, source)
    return PrlResponse(data=data, metadata=metadata)


@router.get("/affr", response_model=AffrResponse)
async def affr(
    start: str = Query(default=None),
    end: str = Query(default=None),
    source: str = Query(default="demo"),
):
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")

    data, metadata = get_affr_data(start, end, source)
    return AffrResponse(data=data, metadata=metadata)


@router.get("/statistics", response_model=StatisticsResponse)
async def statistics(
    start: str = Query(default=None),
    end: str = Query(default=None),
    source: str = Query(default="demo"),
):
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")

    stats = get_statistics(start, end, source)
    return StatisticsResponse(**stats)


@router.get("/daily-summary", response_model=DailySummaryResponse)
async def daily_summary(
    start: str = Query(default=None),
    end: str = Query(default=None),
    source: str = Query(default="demo"),
):
    if not start or not end:
        end = datetime.now()
        start = end - timedelta(days=7)
        start = start.strftime("%Y-%m-%d")
        end = end.strftime("%Y-%m-%d")

    summary = get_daily_summary(start, end, source)
    return DailySummaryResponse(**summary)


@router.post("/upload", response_model=UploadResponse)
async def upload(
    type: str = Query(default="prl"),
    file: UploadFile = File(...),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien erlaubt")

    contents = await file.read()
    result = parse_csv_to_preview(contents)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "CSV konnte nicht geparst werden"))

    return UploadResponse(
        success=True,
        rows=result["rows"],
        columns=result["columns"],
        preview=result["preview"],
    )
