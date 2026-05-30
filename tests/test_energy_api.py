import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from backend.services import energy_service


def _make_mock_fetcher():
    fetcher = MagicMock()
    dates = pd.date_range("2024-06-01", "2024-06-08", freq="15min", inclusive="left")
    prl_df = pd.DataFrame({
        "Timestamp": dates,
        "Deutschland_Positiv_MW": 584.0,
        "Deutschland_Negativ_MW": 584.0,
        "Preis_EUR_per_MW": 33.36,
    }).set_index("Timestamp")
    affr_df = pd.DataFrame({
        "Timestamp": dates,
        "Deutschland_Positiv_MW": np.random.uniform(1500, 2500, len(dates)),
        "Deutschland_Negativ_MW": np.random.uniform(1500, 2500, len(dates)),
    }).set_index("Timestamp")
    fetcher.get_prl_dataframe.return_value = prl_df
    fetcher.get_affr_dataframe.return_value = affr_df
    fetcher.get_last_fallback_date.return_value = None
    return fetcher


class TestEnergyAPI:
    BASE = "/api/energy"

    def test_health_endpoint(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_get_prl_endpoint(self, client, date_range):
        r = client.get(
            f"{self.BASE}/prl",
            params={
                "start": date_range["start"],
                "end": date_range["end"],
                "source": "demo",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert len(body["data"]) > 0
        assert "metadata" in body
        assert body["metadata"]["source"] == "demo"

    def test_get_prl_endpoint_defaults_to_7_days(self, client):
        r = client.get(f"{self.BASE}/prl")
        assert r.status_code == 200
        body = r.json()
        assert len(body["data"]) > 0

    def test_get_prl_record_has_required_fields(self, client, date_range):
        r = client.get(
            f"{self.BASE}/prl",
            params={"start": date_range["start"], "end": date_range["end"]},
        )
        record = r.json()["data"][0]
        assert "timestamp" in record
        assert "deutschland_positiv_mw" in record
        assert "deutschland_negativ_mw" in record

    def test_get_affr_endpoint(self, client, date_range):
        r = client.get(
            f"{self.BASE}/affr",
            params={
                "start": date_range["start"],
                "end": date_range["end"],
                "source": "demo",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert len(body["data"]) > 0
        assert "deutschland_positiv_mw" in body["data"][0]

    def test_get_statistics_endpoint(self, client, date_range):
        r = client.get(
            f"{self.BASE}/statistics",
            params={"start": date_range["start"], "end": date_range["end"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert "prl" in body
        assert "affr" in body
        assert body["prl"]["total_intervals"] > 0

    def test_get_daily_summary_endpoint(self, client, date_range):
        r = client.get(
            f"{self.BASE}/daily-summary",
            params={"start": date_range["start"], "end": date_range["end"]},
        )
        assert r.status_code == 200
        body = r.json()
        assert "prl_daily" in body
        assert "affr_daily" in body
        assert len(body["prl_daily"]) > 0

    def test_upload_invalid_file_returns_400(self, client):
        r = client.post(
            f"{self.BASE}/upload",
            params={"type": "prl"},
            files={"file": ("test.txt", b"not a csv", "text/plain")},
        )
        assert r.status_code == 400
        assert "Nur CSV" in r.json()["detail"]

    def test_upload_valid_csv(self, client):
        csv_content = "Timestamp;Wert\n2024-01-01;10.5\n2024-01-02;20.3\n"
        r = client.post(
            f"{self.BASE}/upload",
            params={"type": "prl"},
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["rows"] == 2
        assert "Timestamp" in body["columns"]

    def test_get_prl_endpoint_api_source(self, client, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            r = client.get(
                f"{self.BASE}/prl",
                params={
                    "start": date_range["start"],
                    "end": date_range["end"],
                    "source": "api",
                },
            )
        assert r.status_code == 200
        body = r.json()
        assert body["metadata"]["source"] == "api"
        assert body["data"][0]["deutschland_positiv_mw"] == 584.0

    def test_get_affr_endpoint_api_source(self, client, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            r = client.get(
                f"{self.BASE}/affr",
                params={
                    "start": date_range["start"],
                    "end": date_range["end"],
                    "source": "api",
                },
            )
        assert r.status_code == 200
        body = r.json()
        assert body["metadata"]["source"] == "api"

    def test_get_statistics_endpoint_api_source(self, client, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            r = client.get(
                f"{self.BASE}/statistics",
                params={
                    "start": date_range["start"],
                    "end": date_range["end"],
                    "source": "api",
                },
            )
        assert r.status_code == 200
        body = r.json()
        assert body["prl"]["mean_positive"] == 584.0

    def test_get_daily_summary_endpoint_api_source(self, client, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            r = client.get(
                f"{self.BASE}/daily-summary",
                params={
                    "start": date_range["start"],
                    "end": date_range["end"],
                    "source": "api",
                },
            )
        assert r.status_code == 200
        body = r.json()
        assert "prl_daily" in body
        assert "affr_daily" in body
