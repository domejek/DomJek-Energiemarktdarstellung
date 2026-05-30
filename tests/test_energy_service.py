import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime

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
        "Energiepreis_Positiv_EUR_per_MWh": np.random.uniform(10, 100, len(dates)),
        "Energiepreis_Negativ_EUR_per_MWh": np.random.uniform(-100, -10, len(dates)),
    }).set_index("Timestamp")
    fetcher.get_prl_dataframe.return_value = prl_df
    fetcher.get_affr_dataframe.return_value = affr_df
    fetcher.get_last_fallback_date.return_value = None
    return fetcher


class TestEnergyService:
    def test_get_prl_data_returns_records(self, date_range):
        data, metadata = energy_service.get_prl_data(
            date_range["start"], date_range["end"]
        )
        assert len(data) > 0
        assert "timestamp" in data[0]
        assert "deutschland_positiv_mw" in data[0]
        assert metadata["interval_count"] == len(data)

    def test_get_prl_data_date_filtering(self):
        data, _ = energy_service.get_prl_data("2024-06-01", "2024-06-02")
        assert len(data) > 0
        dates_in_range = {r["timestamp"][:10] for r in data}
        assert "2024-06-01" in dates_in_range
        assert "2024-06-02" in dates_in_range
        assert len(dates_in_range) == 2

    def test_get_prl_data_single_day_has_96_intervals(self):
        data, metadata = energy_service.get_prl_data("2024-06-01", "2024-06-01")
        assert len(data) == 96
        assert metadata["interval_count"] == 96

    def test_get_affr_data_returns_records(self, date_range):
        data, metadata = energy_service.get_affr_data(
            date_range["start"], date_range["end"]
        )
        assert len(data) > 0
        assert "deutschland_positiv_mw" in data[0]
        assert "deutschland_negativ_mw" in data[0]

    def test_get_statistics_returns_all_keys(self, date_range):
        stats = energy_service.get_statistics(
            date_range["start"], date_range["end"]
        )
        assert "prl" in stats
        assert "affr" in stats
        assert "mean_positive" in stats["prl"]
        assert "max_positive" in stats["prl"]
        assert "std_positive" in stats["prl"]
        assert "total_intervals" in stats["prl"]
        assert "mean_activation" in stats["affr"]
        assert "total_activated_mwh" in stats["affr"]
        assert "activation_rate" in stats["affr"]

    def test_get_statistics_values_are_plausible(self, date_range):
        stats = energy_service.get_statistics(
            date_range["start"], date_range["end"]
        )
        assert -100 < stats["prl"]["mean_positive"] < 100
        assert -100 < stats["prl"]["mean_negative"] < 100
        assert stats["affr"]["mean_activation"] >= 0
        assert 0 <= stats["affr"]["activation_rate"] <= 100
        assert stats["prl"]["total_intervals"] > 0

    def test_get_statistics_reproducible_with_seed(self, date_range):
        stats1 = energy_service.get_statistics(
            date_range["start"], date_range["end"]
        )
        np = pytest.importorskip("numpy")
        np.random.seed(42)
        stats2 = energy_service.get_statistics(
            date_range["start"], date_range["end"]
        )
        assert stats1["prl"]["mean_positive"] == stats2["prl"]["mean_positive"]

    def test_get_daily_summary_structure(self, date_range):
        summary = energy_service.get_daily_summary(
            date_range["start"], date_range["end"]
        )
        assert "prl_daily" in summary
        assert "affr_daily" in summary
        assert len(summary["prl_daily"]) > 0
        assert "date" in summary["prl_daily"][0]

    def test_get_daily_summary_date_range(self, date_range):
        summary = energy_service.get_daily_summary(
            date_range["start"], date_range["end"]
        )
        dates = [d["date"] for d in summary["prl_daily"]]
        assert len(dates) > 0
        for d in dates:
            assert d >= date_range["start"]

    def test_prl_data_default_source_is_demo(self, date_range):
        data, metadata = energy_service.get_prl_data(
            date_range["start"], date_range["end"]
        )
        assert metadata["source"] == "demo"

    def test_prl_data_api_source_uses_fetcher(self, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            data, metadata = energy_service.get_prl_data(
                date_range["start"], date_range["end"], source="api"
            )
        assert len(data) > 0
        assert metadata["source"] == "api"
        assert data[0]["deutschland_positiv_mw"] == 584.0

    def test_prl_data_api_fallback_to_demo_on_failure(self, date_range):
        failing_fetcher = MagicMock()
        failing_fetcher.get_prl_dataframe.side_effect = ValueError("API down")
        with patch.object(energy_service, "_get_fetcher", return_value=failing_fetcher):
            data, metadata = energy_service.get_prl_data(
                date_range["start"], date_range["end"], source="api"
            )
        assert len(data) > 0
        assert metadata["source"] == "demo_fallback"

    def test_affr_data_api_source_uses_fetcher(self, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            data, metadata = energy_service.get_affr_data(
                date_range["start"], date_range["end"], source="api"
            )
        assert len(data) > 0
        assert metadata["source"] == "api"

    def test_statistics_api_source(self, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            stats = energy_service.get_statistics(
                date_range["start"], date_range["end"], source="api"
            )
        assert stats["prl"]["mean_positive"] == 584.0

    def test_daily_summary_api_source(self, date_range):
        mock_fetcher = _make_mock_fetcher()
        with patch.object(energy_service, "_get_fetcher", return_value=mock_fetcher):
            summary = energy_service.get_daily_summary(
                date_range["start"], date_range["end"], source="api"
            )
        assert "prl_daily" in summary
        assert "affr_daily" in summary
