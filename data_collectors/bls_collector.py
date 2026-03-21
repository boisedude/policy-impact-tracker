"""
BLS (Bureau of Labor Statistics) Data Collector

Pulls state-level employment data from the BLS Public Data API v2,
including LAUS (Local Area Unemployment Statistics) and CES
(Current Employment Statistics) data.

API Key: Free at https://data.bls.gov/registrationEngine/
Rate Limits: v2 (with key): 500 queries/day, 50 series/query, 20 years/query
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# State FIPS codes for BLS series construction
STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

# LAUS measure codes
LAUS_MEASURES = {
    "03": {"name": "Unemployment Rate", "unit": "Percent"},
    "04": {"name": "Unemployment Count", "unit": "Persons"},
    "05": {"name": "Employment Count", "unit": "Persons"},
    "06": {"name": "Labor Force", "unit": "Persons"},
}

# National CES series
NATIONAL_CES_SERIES = {
    "CES0000000001": {"name": "Total Nonfarm Employment", "unit": "Thousands"},
    "CES3000000001": {"name": "Manufacturing Employment", "unit": "Thousands"},
    "CES1000000001": {"name": "Mining & Logging Employment", "unit": "Thousands"},
    "CES2000000001": {"name": "Construction Employment", "unit": "Thousands"},
    "CES4000000001": {"name": "Trade, Transport & Utilities Employment", "unit": "Thousands"},
    "CES5000000001": {"name": "Information Employment", "unit": "Thousands"},
    "CES5500000001": {"name": "Financial Activities Employment", "unit": "Thousands"},
    "CES6000000001": {"name": "Professional & Business Services Employment", "unit": "Thousands"},
    "CES6500000001": {"name": "Education & Health Services Employment", "unit": "Thousands"},
    "CES7000000001": {"name": "Leisure & Hospitality Employment", "unit": "Thousands"},
    "CES0500000003": {"name": "Average Hourly Earnings (Private)", "unit": "Dollars"},
}


class BLSCollector:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("BLS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BLS API key required. Get one free at: "
                "https://data.bls.gov/registrationEngine/"
            )
        self.session = requests.Session()

    def _fetch_series_batch(
        self,
        series_ids: list[str],
        start_year: int = 2010,
        end_year: int = 2025,
    ) -> dict:
        """Fetch up to 50 series in one API call."""
        payload = {
            "seriesid": series_ids[:50],
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": self.api_key,
        }
        resp = self.session.post(BLS_API_URL, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()

        if result.get("status") != "REQUEST_SUCCEEDED":
            print(f"  BLS API warning: {result.get('message', ['Unknown error'])}")

        return result

    def _parse_bls_response(self, result: dict) -> dict[str, pd.DataFrame]:
        """Parse BLS API response into {series_id: DataFrame}."""
        series_data = {}
        for series in result.get("Results", {}).get("series", []):
            sid = series["seriesID"]
            rows = []
            for obs in series.get("data", []):
                year = int(obs["year"])
                period = obs["period"]
                # Skip annual averages (M13)
                if period == "M13":
                    continue
                month = int(period.replace("M", ""))
                date = pd.Timestamp(year=year, month=month, day=1)
                value = pd.to_numeric(obs["value"].replace(",", ""), errors="coerce")
                rows.append({"date": date, "value": value})
            if rows:
                df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
                df = df.dropna(subset=["value"])
                series_data[sid] = df
        return series_data

    def collect_state_unemployment(
        self,
        states: list[str] = None,
        output_dir: str = "sample_data",
        start_year: int = 2010,
        end_year: int = 2025,
    ) -> pd.DataFrame:
        """Collect LAUS unemployment data for states."""
        if states is None:
            states = list(STATE_FIPS.keys())

        print(f"Collecting BLS LAUS data for {len(states)} states...")
        all_data = []

        # Build series IDs for all states and measures
        series_map = {}
        for state in states:
            state = state.upper()
            fips = STATE_FIPS.get(state)
            if not fips:
                print(f"  Warning: Unknown state {state}")
                continue
            for measure_code, meta in LAUS_MEASURES.items():
                # LAUS series format: LAUST{FIPS}0000000000{measure}
                series_id = f"LAUST{fips}0000000000{measure_code}"
                series_map[series_id] = {
                    "state": state,
                    "state_name": STATE_NAMES[state],
                    "indicator": meta["name"],
                    "unit": meta["unit"],
                }

        # Batch into groups of 50 (BLS limit)
        series_ids = list(series_map.keys())
        for i in range(0, len(series_ids), 50):
            batch = series_ids[i : i + 50]
            print(f"  Fetching batch {i // 50 + 1} ({len(batch)} series)...")
            result = self._fetch_series_batch(batch, start_year, end_year)
            parsed = self._parse_bls_response(result)

            for sid, df in parsed.items():
                meta = series_map[sid]
                df["series_id"] = sid
                df["indicator_name"] = meta["indicator"]
                df["unit"] = meta["unit"]
                df["geography"] = meta["state_name"]
                df["state_code"] = meta["state"]
                df["geo_level"] = "State"
                df["source"] = "BLS LAUS"
                all_data.append(df)

            if i + 50 < len(series_ids):
                time.sleep(1)

        if not all_data:
            print("  No LAUS data collected.")
            return pd.DataFrame()

        combined = pd.concat(all_data, ignore_index=True)
        output_path = Path(output_dir) / "bls_state_employment.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(output_path, index=False)
        print(f"  Saved {len(combined)} records to {output_path}")
        return combined

    def collect_national_industry(
        self,
        output_dir: str = "sample_data",
        start_year: int = 2010,
        end_year: int = 2025,
    ) -> pd.DataFrame:
        """Collect national industry employment breakdown from CES."""
        print("Collecting BLS CES national industry employment...")
        series_ids = list(NATIONAL_CES_SERIES.keys())
        result = self._fetch_series_batch(series_ids, start_year, end_year)
        parsed = self._parse_bls_response(result)

        all_data = []
        for sid, df in parsed.items():
            meta = NATIONAL_CES_SERIES[sid]
            df["series_id"] = sid
            df["indicator_name"] = meta["name"]
            df["unit"] = meta["unit"]
            df["geography"] = "United States"
            df["geo_level"] = "National"
            df["source"] = "BLS CES"
            all_data.append(df)

        if not all_data:
            print("  No CES data collected.")
            return pd.DataFrame()

        combined = pd.concat(all_data, ignore_index=True)
        output_path = Path(output_dir) / "bls_national_industry.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(output_path, index=False)
        print(f"  Saved {len(combined)} records to {output_path}")
        return combined


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Collect BLS employment data")
    parser.add_argument("--output-dir", default="sample_data")
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--states", nargs="*", default=None,
        help="State codes (e.g., ID TX CA). Omit for all states.",
    )
    args = parser.parse_args()

    collector = BLSCollector()
    collector.collect_state_unemployment(
        states=args.states,
        output_dir=args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    collector.collect_national_industry(
        output_dir=args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year,
    )


if __name__ == "__main__":
    main()
