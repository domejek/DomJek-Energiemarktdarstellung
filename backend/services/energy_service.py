import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, List, Optional
import pandas as pd
import numpy as np

from backend.services.regelleistung_api import RegelleistungApiFetcher

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

_fetcher: Optional[RegelleistungApiFetcher] = None


def _get_fetcher() -> RegelleistungApiFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = RegelleistungApiFetcher()
    return _fetcher


def _parse_dates(start_str: str, end_str: str) -> Tuple[datetime, datetime]:
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end_exclusive = datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)
    return start, end_exclusive


def _date_range_days(start: datetime, end_exclusive: datetime) -> pd.DatetimeIndex:
    return pd.date_range(start=start, end=end_exclusive, freq="15min", inclusive="left")


def _df_to_prl_records(df: pd.DataFrame) -> list:
    df = df.reset_index()
    if "Timestamp" in df.columns:
        df["timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S")
        df = df.drop(columns=["Timestamp"])
    else:
        df["timestamp"] = df.index.strftime("%Y-%m-%dT%H:%M:%S")

    for col in df.select_dtypes(include=["float64", "float32"]).columns:
        df[col] = df[col].where(df[col].notna(), None)

    rename_map = {}
    for col in df.columns:
        new_key = col.lower().replace(" ", "_").replace(".", "").replace("(", "").replace(")", "")
        if new_key != col:
            rename_map[col] = new_key
    df = df.rename(columns=rename_map)

    return df.to_dict(orient="records")


def get_prl_data(start_str: str, end_str: str, source: str = "demo") -> Tuple[list, dict]:
    start, end_exclusive = _parse_dates(start_str, end_str)
    dates = _date_range_days(start, end_exclusive)

    effective_source = source

    if source == "api":
        try:
            fetcher = _get_fetcher()
            prl_df = fetcher.get_prl_dataframe(start_str, end_str)
            fallback = fetcher.get_last_fallback_date()
            effective_source = f"api_fallback_{fallback}" if fallback else "api"
            records = _df_to_prl_records(prl_df)
            return records, {"interval_count": len(records), "source": effective_source}
        except Exception:
            effective_source = "demo_fallback"

    prl_df = pd.DataFrame({
        "Timestamp": dates,
        "Deutschland_Positiv_MW": np.random.normal(0, 20, len(dates)),
        "Deutschland_Negativ_MW": np.random.normal(0, 20, len(dates)),
        "50Hertz_MW": np.random.normal(0, 8, len(dates)),
        "Amprion_MW": np.random.normal(0, 10, len(dates)),
        "TenneT_MW": np.random.normal(0, 9, len(dates)),
        "TransnetBW_MW": np.random.normal(0, 7, len(dates)),
    }).set_index("Timestamp")

    records = _df_to_prl_records(prl_df)
    return records, {"interval_count": len(records), "source": effective_source}


def get_affr_data(start_str: str, end_str: str, source: str = "demo") -> Tuple[list, dict]:
    start, end_exclusive = _parse_dates(start_str, end_str)
    dates = _date_range_days(start, end_exclusive)

    effective_source = source

    if source == "api":
        try:
            fetcher = _get_fetcher()
            affr_df = fetcher.get_affr_dataframe(start_str, end_str)
            fallback = fetcher.get_last_fallback_date()
            effective_source = f"api_fallback_{fallback}" if fallback else "api"
            records = _df_to_prl_records(affr_df)
            return records, {"interval_count": len(records), "source": effective_source}
        except Exception:
            effective_source = "demo_fallback"

    affr_df = pd.DataFrame({
        "Timestamp": dates,
        "Deutschland_Positiv_MW": np.random.exponential(50, len(dates)).clip(0, 800),
        "Deutschland_Negativ_MW": np.random.exponential(30, len(dates)).clip(0, 500),
        "50Hertz_Positiv_MW": np.random.exponential(15, len(dates)),
        "Amprion_Positiv_MW": np.random.exponential(18, len(dates)),
        "TenneT_Positiv_MW": np.random.exponential(16, len(dates)),
        "TransnetBW_Positiv_MW": np.random.exponential(12, len(dates)),
    }).set_index("Timestamp")

    records = _df_to_prl_records(affr_df)
    return records, {"interval_count": len(records), "source": effective_source}


def get_statistics(start_str: str, end_str: str, source: str = "demo") -> dict:
    start, end_exclusive = _parse_dates(start_str, end_str)
    dates = _date_range_days(start, end_exclusive)

    if source == "api":
        try:
            fetcher = _get_fetcher()
            prl_df = fetcher.get_prl_dataframe(start_str, end_str)
            affr_df = fetcher.get_affr_dataframe(start_str, end_str)
        except Exception:
            prl_df = None
            affr_df = None
    else:
        prl_df = None
        affr_df = None

    if prl_df is None:
        prl_df = pd.DataFrame({
            "Deutschland_Positiv_MW": np.random.normal(0, 20, len(dates)),
            "Deutschland_Negativ_MW": np.random.normal(0, 20, len(dates)),
        }, index=dates)

    if affr_df is None:
        affr_df = pd.DataFrame({
            "Deutschland_Positiv_MW": np.random.exponential(50, len(dates)).clip(0, 800),
            "Deutschland_Negativ_MW": np.random.exponential(30, len(dates)).clip(0, 500),
        }, index=dates)

    stats = {
        "prl": {
            "mean_positive": round(float(prl_df["Deutschland_Positiv_MW"].mean()), 2),
            "mean_negative": round(float(prl_df["Deutschland_Negativ_MW"].mean()), 2),
            "max_positive": round(float(prl_df["Deutschland_Positiv_MW"].max()), 2),
            "max_negative": round(float(prl_df["Deutschland_Negativ_MW"].min()), 2),
            "std_positive": round(float(prl_df["Deutschland_Positiv_MW"].std()), 2),
            "total_intervals": len(prl_df),
        },
        "affr": {
            "mean_activation": round(float(affr_df["Deutschland_Positiv_MW"].mean()), 2),
            "max_activation": round(float(affr_df["Deutschland_Positiv_MW"].max()), 2),
            "total_activated_mwh": round(float(affr_df["Deutschland_Positiv_MW"].sum() * 0.25), 2),
            "activation_rate": round(float((affr_df["Deutschland_Positiv_MW"] > 0).sum() / len(affr_df) * 100), 2),
        },
    }
    return stats


def get_daily_summary(start_str: str, end_str: str, source: str = "demo") -> dict:
    start, end_exclusive = _parse_dates(start_str, end_str)
    dates = _date_range_days(start, end_exclusive)

    if source == "api":
        try:
            fetcher = _get_fetcher()
            prl_df = fetcher.get_prl_dataframe(start_str, end_str)
            affr_df = fetcher.get_affr_dataframe(start_str, end_str)
        except Exception:
            prl_df = None
            affr_df = None
    else:
        prl_df = None
        affr_df = None

    if prl_df is None:
        prl_df = pd.DataFrame({
            "Deutschland_Positiv_MW": np.random.normal(0, 20, len(dates)),
            "Deutschland_Negativ_MW": np.random.normal(0, 20, len(dates)),
        }, index=dates)

    if affr_df is None:
        affr_df = pd.DataFrame({
            "Deutschland_Positiv_MW": np.random.exponential(50, len(dates)).clip(0, 800),
            "Deutschland_Negativ_MW": np.random.exponential(30, len(dates)).clip(0, 500),
        }, index=dates)

    prl_daily = prl_df.resample("D").agg({
        "Deutschland_Positiv_MW": ["mean", "max", "min"],
        "Deutschland_Negativ_MW": ["mean", "max", "min"],
    })
    prl_daily.columns = ["pos_mean", "pos_max", "pos_min", "neg_mean", "neg_max", "neg_min"]
    prl_daily.index = prl_daily.index.strftime("%Y-%m-%d")

    affr_daily = affr_df.resample("D").agg({
        "Deutschland_Positiv_MW": ["mean", "max", "sum"],
        "Deutschland_Negativ_MW": ["mean", "max", "sum"],
    })
    affr_daily.columns = ["pos_mean", "pos_max", "pos_sum", "neg_mean", "neg_max", "neg_sum"]
    affr_daily.index = affr_daily.index.strftime("%Y-%m-%d")

    return {
        "prl_daily": prl_daily.reset_index().rename(columns={"index": "date"}).to_dict(orient="records"),
        "affr_daily": affr_daily.reset_index().rename(columns={"index": "date"}).to_dict(orient="records"),
    }


def parse_csv_to_preview(file_bytes: bytes, sep: str = ";", decimal: str = ",") -> dict:
    import io
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, decimal=decimal, nrows=20)
        return {
            "success": True,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient="records"),
        }
    except Exception as e:
        return {
            "success": False,
            "rows": 0,
            "columns": [],
            "preview": [],
            "error": str(e),
        }
