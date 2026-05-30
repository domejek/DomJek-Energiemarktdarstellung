import io
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.regelleistung.net/apps/crds/api/v2"

URLS = {
    "fcr_demands": f"{BASE_URL}/tenders/demands?&productType=FCR&market=CAPACITY&exportFormat=xlsx&deliveryDate={{date}}",
    "fcr_results": f"{BASE_URL}/tenders/results/aggregated?&productType=FCR&market=CAPACITY&exportFormat=xlsx&deliveryDate={{date}}",
    "affr_cap_demands": f"{BASE_URL}/tenders/demands?&productType=aFRR&market=CAPACITY&exportFormat=xlsx&deliveryDate={{date}}",
    "affr_cap_results": f"{BASE_URL}/tenders/results/aggregated?&productType=aFRR&market=CAPACITY&exportFormat=xlsx&deliveryDate={{date}}",
    "affr_energy_demands": f"{BASE_URL}/tenders/demands?&productType=aFRR&market=ENERGY&exportFormat=xlsx&deliveryDate={{date}}",
    "affr_energy_results": f"{BASE_URL}/tenders/results/aggregated?&productType=aFRR&market=ENERGY&exportFormat=xlsx&deliveryDate={{date}}",
}

FCR_BLOCKS = [
    ("NEGPOS_00_04", 0, 4),
    ("NEGPOS_04_08", 4, 8),
    ("NEGPOS_08_12", 8, 12),
    ("NEGPOS_12_16", 12, 16),
    ("NEGPOS_16_20", 16, 20),
    ("NEGPOS_20_24", 20, 24),
]

AFRR_BLOCKS = [
    ("00_04", 0, 4),
    ("04_08", 4, 8),
    ("08_12", 8, 12),
    ("12_16", 12, 16),
    ("16_20", 16, 20),
    ("20_24", 20, 24),
]


class RegelleistungApiFetcher:
    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()
        self._session.headers.update({
            "User-Agent": "Energiemarktdarstellung/3.0",
            "Accept": "application/octet-stream",
        })
        self._cache: dict[str, dict] = {}
        self._used_fallback_date: Optional[str] = None

    def _fetch_xlsx(self, url: str, max_retries: int = 2) -> Optional[bytes]:
        for attempt in range(max_retries):
            try:
                resp = self._session.get(url, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 100:
                    return resp.content
                logger.warning("Fetch %s attempt %d: status=%d size=%d",
                               url, attempt + 1, resp.status_code, len(resp.content))
            except requests.RequestException as e:
                logger.warning("Fetch %s attempt %d failed: %s", url, attempt + 1, e)
        return None

    def _get_effective_date(self, date_str: str, max_lookback: int = 7) -> str:
        if date_str in self._cache:
            return date_str

        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        for offset in range(max_lookback):
            check = (parsed - timedelta(days=offset)).strftime("%Y-%m-%d")
            if check in self._cache:
                return check

            test_url = URLS["fcr_demands"].format(date=check)
            content = self._fetch_xlsx(test_url)
            if content is not None:
                self._used_fallback_date = check if offset > 0 else None
                return check

        raise ValueError(f"Keine Daten verfuegbar ab {date_str} (Rueckschau: {max_lookback} Tage)")

    def _fetch_date(self, date_str: str) -> dict:
        if date_str in self._cache:
            return self._cache[date_str]

        raw = {}
        for key, url_template in URLS.items():
            url = url_template.format(date=date_str)
            content = self._fetch_xlsx(url)
            if content is not None:
                try:
                    df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
                    raw[key] = df
                except Exception as e:
                    logger.warning("Parse %s for %s failed: %s", key, date_str, e)

        if not raw:
            raise ValueError(f"Keine Daten fuer {date_str} abrufbar")

        self._cache[date_str] = raw
        return raw

    def _expand_fcr_to_15min(self, raw: dict, date_str: str) -> pd.DataFrame:
        demands = raw.get("fcr_demands")
        results = raw.get("fcr_results")

        timestamps = pd.date_range(
            start=date_str, end=pd.Timestamp(date_str) + timedelta(days=1),
            freq="15min", inclusive="left"
        )

        pos_values = {}
        neg_values = {}
        price_map = {}

        for product_name, start_h, end_h in FCR_BLOCKS:
            if demands is not None:
                row = demands[demands["PRODUCT"] == product_name]
                if not row.empty:
                    val = row["GERMANY_COUNTRY_DEMAND_[MW]"].iloc[0]
                    if pd.isna(val) or val == "-":
                        val = row["TOTAL_DEMAND_[MW]"].iloc[0]
                    pos_values[product_name] = float(val)
                    neg_values[product_name] = float(val)
                else:
                    pos_values[product_name] = None
                    neg_values[product_name] = None
            else:
                pos_values[product_name] = None
                neg_values[product_name] = None

            if results is not None:
                prod_col = "PRODUCTNAME" if "PRODUCTNAME" in results.columns else "PRODUCT"
                row = results[results[prod_col] == product_name]
                if not row.empty and "GERMANY_SETTLEMENTCAPACITY_PRICE_[EUR/MW]" in row.columns:
                    price_map[product_name] = float(row["GERMANY_SETTLEMENTCAPACITY_PRICE_[EUR/MW]"].iloc[0])
                else:
                    price_map[product_name] = None
            else:
                price_map[product_name] = None

        rows = []
        ts_offset = 0
        for product_name, start_h, end_h in FCR_BLOCKS:
            for i in range(start_h * 4, end_h * 4):
                ts = timestamps[i]
                rows.append({
                    "Timestamp": ts,
                    "Deutschland_Positiv_MW": pos_values.get(product_name),
                    "Deutschland_Negativ_MW": neg_values.get(product_name),
                    "Preis_EUR_per_MW": price_map.get(product_name),
                })
            ts_offset += end_h * 4 - start_h * 4

        df = pd.DataFrame(rows).set_index("Timestamp")
        df.index = pd.to_datetime(df.index)
        return df

    def _build_affr_15min(self, raw: dict, date_str: str) -> pd.DataFrame:
        energy_demands = raw.get("affr_energy_demands")
        energy_results = raw.get("affr_energy_results")

        timestamps = pd.date_range(
            start=date_str, end=pd.Timestamp(date_str) + timedelta(days=1),
            freq="15min", inclusive="left"
        )

        def parse_product(product_label: str) -> Optional[int]:
            parts = product_label.split("_")
            if len(parts) >= 2:
                try:
                    return int(parts[-1])
                except ValueError:
                    return None
            return None

        pos_demand = {}
        neg_demand = {}
        pos_price = {}
        neg_price = {}
        pos_offered = {}
        neg_offered = {}

        if energy_demands is not None:
            for _, row in energy_demands.iterrows():
                prod = row["PRODUCT"]
                idx = parse_product(prod)
                if idx is None:
                    continue
                val = float(row["TOTAL_DEMAND_[MW]"])
                if prod.startswith("POS_"):
                    pos_demand[idx] = val
                elif prod.startswith("NEG_"):
                    neg_demand[idx] = val

        if energy_results is not None:
            for _, row in energy_results.iterrows():
                prod = row["PRODUCT"]
                idx = parse_product(prod)
                if idx is None:
                    continue
                if "GERMANY_MARGINAL_ENERGY_PRICE_[EUR/MWh]" in energy_results.columns:
                    price = row.get("GERMANY_MARGINAL_ENERGY_PRICE_[EUR/MWh]")
                    price_val = float(price) if pd.notna(price) else None
                else:
                    price_val = None

                offered = row.get("GERMANY_SUM_OF_OFFERED_CAPACITY_[MW]")
                offered_val = float(offered) if pd.notna(offered) else None

                if prod.startswith("POS_"):
                    pos_price[idx] = price_val
                    pos_offered[idx] = offered_val
                elif prod.startswith("NEG_"):
                    neg_price[idx] = price_val
                    neg_offered[idx] = offered_val

        rows = []
        for i in range(96):
            idx = i + 1
            ts = timestamps[i]
            rows.append({
                "Timestamp": ts,
                "Deutschland_Positiv_MW": pos_demand.get(idx),
                "Deutschland_Negativ_MW": neg_demand.get(idx),
                "Energiepreis_Positiv_EUR_per_MWh": pos_price.get(idx),
                "Energiepreis_Negativ_EUR_per_MWh": neg_price.get(idx),
                "Angebotene_Kapazitaet_Positiv_MW": pos_offered.get(idx),
                "Angebotene_Kapazitaet_Negativ_MW": neg_offered.get(idx),
            })

        df = pd.DataFrame(rows).set_index("Timestamp")
        df.index = pd.to_datetime(df.index)
        return df

    def get_prl_dataframe(self, start: str, end: str) -> pd.DataFrame:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        all_dfs = []
        current = start_dt
        while current <= end_dt:
            date_str = current.strftime("%Y-%m-%d")
            try:
                effective = self._get_effective_date(date_str)
                raw = self._fetch_date(effective)
                day_df = self._expand_fcr_to_15min(raw, date_str)
                all_dfs.append(day_df)
            except ValueError as e:
                logger.warning("No data for %s: %s", date_str, e)
            current += timedelta(days=1)

        if not all_dfs:
            raise ValueError(f"Keine PRL-Daten fuer {start} bis {end} verfuegbar")

        result = pd.concat(all_dfs)
        result.index.name = "Timestamp"
        return result

    def get_affr_dataframe(self, start: str, end: str) -> pd.DataFrame:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        all_dfs = []
        current = start_dt
        while current <= end_dt:
            date_str = current.strftime("%Y-%m-%d")
            try:
                effective = self._get_effective_date(date_str)
                raw = self._fetch_date(effective)
                day_df = self._build_affr_15min(raw, date_str)
                all_dfs.append(day_df)
            except ValueError as e:
                logger.warning("No data for %s: %s", date_str, e)
            current += timedelta(days=1)

        if not all_dfs:
            raise ValueError(f"Keine aFRR-Daten fuer {start} bis {end} verfuegbar")

        result = pd.concat(all_dfs)
        result.index.name = "Timestamp"
        return result

    def get_last_fallback_date(self) -> Optional[str]:
        return self._used_fallback_date
