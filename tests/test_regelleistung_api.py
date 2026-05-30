import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.services.regelleistung_api import RegelleistungApiFetcher, FCR_BLOCKS


class TestFcrParsing:
    def test_expand_fcr_to_15min_creates_96_rows(self):
        fetcher = RegelleistungApiFetcher()
        date_str = "2024-06-01"

        demands = pd.DataFrame({
            "PRODUCT": [f"NEGPOS_{h:02d}_{h+4:02d}" for h in range(0, 24, 4)],
            "GERMANY_COUNTRY_DEMAND_[MW]": [584, 584, 584, 584, 584, 584],
            "TOTAL_DEMAND_[MW]": [1704, 1704, 1704, 1704, 1704, 1704],
        })
        results = pd.DataFrame({
            "PRODUCTNAME": [f"NEGPOS_{h:02d}_{h+4:02d}" for h in range(0, 24, 4)],
            "GERMANY_SETTLEMENTCAPACITY_PRICE_[EUR/MW]": [33.36, 47.46, 152.25, 197.60, 100.00, 85.00],
            "GERMANY_DEMAND_[MW]": [584, 584, 584, 584, 584, 584],
        })

        raw = {"fcr_demands": demands, "fcr_results": results}
        df = fetcher._expand_fcr_to_15min(raw, date_str)

        assert len(df) == 96
        assert df.index.name == "Timestamp"
        assert "Deutschland_Positiv_MW" in df.columns
        assert "Deutschland_Negativ_MW" in df.columns
        assert "Preis_EUR_per_MW" in df.columns

        assert df["Deutschland_Positiv_MW"].iloc[0] == 584.0
        assert df["Preis_EUR_per_MW"].iloc[0] == 33.36
        assert df["Preis_EUR_per_MW"].iloc[16] == 47.46

    def test_expand_fcr_no_results_falls_back_gracefully(self):
        fetcher = RegelleistungApiFetcher()
        date_str = "2024-06-01"

        demands = pd.DataFrame({
            "PRODUCT": [f"NEGPOS_{h:02d}_{h+4:02d}" for h in range(0, 24, 4)],
            "GERMANY_COUNTRY_DEMAND_[MW]": [584] * 6,
        })

        raw = {"fcr_demands": demands}
        df = fetcher._expand_fcr_to_15min(raw, date_str)

        assert len(df) == 96
        assert df["Preis_EUR_per_MW"].isna().all()

    def test_expand_fcr_handles_dash_in_country_demand(self):
        fetcher = RegelleistungApiFetcher()
        date_str = "2024-06-01"

        demands = pd.DataFrame({
            "PRODUCT": [f"NEGPOS_{h:02d}_{h+4:02d}" for h in range(0, 24, 4)],
            "GERMANY_COUNTRY_DEMAND_[MW]": ["-", 584, 584, 584, 584, 584],
            "TOTAL_DEMAND_[MW]": [1704, 1704, 1704, 1704, 1704, 1704],
        })

        raw = {"fcr_demands": demands}
        df = fetcher._expand_fcr_to_15min(raw, date_str)

        assert df["Deutschland_Positiv_MW"].iloc[0] == 1704.0


class TestAffrParsing:
    def test_build_affr_15min_creates_96_rows(self):
        fetcher = RegelleistungApiFetcher()
        date_str = "2024-06-01"

        pos_rows = []
        neg_rows = []
        for i in range(1, 97):
            pos_rows.append({
                "DELIVERY_DATE": date_str,
                "TYPE_OF_RESERVES": "aFRR",
                "PRODUCT": f"POS_{i:03d}",
                "TOTAL_DEMAND_[MW]": 1900,
            })
            neg_rows.append({
                "DELIVERY_DATE": date_str,
                "TYPE_OF_RESERVES": "aFRR",
                "PRODUCT": f"NEG_{i:03d}",
                "TOTAL_DEMAND_[MW]": 1800,
            })
        energy_demands = pd.DataFrame(pos_rows + neg_rows)

        pos_res = []
        neg_res = []
        for i in range(1, 97):
            pos_res.append({
                "DELIVERY_DATE": date_str,
                "TYPE_OF_RESERVES": "aFRR",
                "PRODUCT": f"POS_{i:03d}",
                "GERMANY_MARGINAL_ENERGY_PRICE_[EUR/MWh]": 50.0 + i,
                "GERMANY_SUM_OF_OFFERED_CAPACITY_[MW]": 4000.0,
            })
            neg_res.append({
                "DELIVERY_DATE": date_str,
                "TYPE_OF_RESERVES": "aFRR",
                "PRODUCT": f"NEG_{i:03d}",
                "GERMANY_MARGINAL_ENERGY_PRICE_[EUR/MWh]": -50.0 - i,
                "GERMANY_SUM_OF_OFFERED_CAPACITY_[MW]": 4000.0,
            })
        energy_results = pd.DataFrame(pos_res + neg_res)

        raw = {"affr_energy_demands": energy_demands, "affr_energy_results": energy_results}
        df = fetcher._build_affr_15min(raw, date_str)

        assert len(df) == 96
        assert "Deutschland_Positiv_MW" in df.columns
        assert "Deutschland_Negativ_MW" in df.columns
        assert "Energiepreis_Positiv_EUR_per_MWh" in df.columns

        assert df["Deutschland_Positiv_MW"].iloc[0] == 1900.0
        assert df["Deutschland_Negativ_MW"].iloc[0] == 1800.0
        assert df["Energiepreis_Positiv_EUR_per_MWh"].iloc[0] == 51.0
        assert df["Energiepreis_Negativ_EUR_per_MWh"].iloc[0] == -51.0

    def test_build_affr_no_results_graceful(self):
        fetcher = RegelleistungApiFetcher()
        date_str = "2024-06-01"

        pos_rows = [{
            "DELIVERY_DATE": date_str, "TYPE_OF_RESERVES": "aFRR",
            "PRODUCT": f"POS_{i:03d}", "TOTAL_DEMAND_[MW]": 1900.0,
        } for i in range(1, 97)]
        neg_rows = [{
            "DELIVERY_DATE": date_str, "TYPE_OF_RESERVES": "aFRR",
            "PRODUCT": f"NEG_{i:03d}", "TOTAL_DEMAND_[MW]": 1800.0,
        } for i in range(1, 97)]
        energy_demands = pd.DataFrame(pos_rows + neg_rows)

        raw = {"affr_energy_demands": energy_demands}
        df = fetcher._build_affr_15min(raw, date_str)

        assert len(df) == 96
        assert df["Energiepreis_Positiv_EUR_per_MWh"].isna().all()


class TestFetcherIntegration:
    def test_get_effective_date_uses_exact_match(self):
        fetcher = RegelleistungApiFetcher()
        fetcher._cache = {"2024-06-01": {"dummy": "data"}}
        result = fetcher._get_effective_date("2024-06-01")
        assert result == "2024-06-01"

    @patch("backend.services.regelleistung_api.requests.Session.get")
    def test_fallback_to_yesterday_on_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = (
            b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  
            + b"\x00" * 200
        )
        mock_get.return_value = mock_resp

        fetcher = RegelleistungApiFetcher()
        result = fetcher._get_effective_date("2024-06-01", max_lookback=3)

        assert mock_get.call_count > 0
        called_dates = []
        for call_args in mock_get.call_args_list:
            url = call_args[0][0]
            if "deliveryDate=" in url:
                d = url.split("deliveryDate=")[-1][:10]
                called_dates.append(d)

        assert "2024-06-01" in called_dates

    @patch("backend.services.regelleistung_api.requests.Session.get")
    def test_all_dates_fail_raises_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.content = b""
        mock_get.return_value = mock_resp

        fetcher = RegelleistungApiFetcher()
        with pytest.raises(ValueError, match="Keine Daten"):
            fetcher._get_effective_date("2024-06-01", max_lookback=2)

    def test_get_prl_dataframe_multiple_days(self):
        fetcher = RegelleistungApiFetcher()

        demands = pd.DataFrame({
            "PRODUCT": [f"NEGPOS_{h:02d}_{h+4:02d}" for h in range(0, 24, 4)],
            "GERMANY_COUNTRY_DEMAND_[MW]": [584] * 6,
        })

        def mock_fetch_date(date_str):
            return {"fcr_demands": demands}

        def mock_eff_date(date_str, max_lookback=7):
            return date_str

        fetcher._fetch_date = mock_fetch_date
        fetcher._get_effective_date = mock_eff_date

        df = fetcher.get_prl_dataframe("2024-06-01", "2024-06-03")

        assert len(df) == 288
        assert (df["Deutschland_Positiv_MW"] == 584.0).all()

    def test_get_affr_dataframe_multiple_days(self):
        fetcher = RegelleistungApiFetcher()

        pos_rows = [{
            "DELIVERY_DATE": "2024-06-01",
            "TYPE_OF_RESERVES": "aFRR",
            "PRODUCT": f"POS_{i:03d}",
            "TOTAL_DEMAND_[MW]": 1900.0,
        } for i in range(1, 97)]
        neg_rows = [{
            "DELIVERY_DATE": "2024-06-01",
            "TYPE_OF_RESERVES": "aFRR",
            "PRODUCT": f"NEG_{i:03d}",
            "TOTAL_DEMAND_[MW]": 1800.0,
        } for i in range(1, 97)]
        energy_demands = pd.DataFrame(pos_rows + neg_rows)

        def mock_fetch_date(date_str):
            return {"affr_energy_demands": energy_demands}

        def mock_eff_date(date_str, max_lookback=7):
            return date_str

        fetcher._fetch_date = mock_fetch_date
        fetcher._get_effective_date = mock_eff_date

        df = fetcher.get_affr_dataframe("2024-06-01", "2024-06-01")

        assert len(df) == 96
        assert df["Deutschland_Positiv_MW"].iloc[0] == 1900.0
