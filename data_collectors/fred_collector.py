"""
FRED (Federal Reserve Economic Data) Collector

Pulls key economic indicator time series from the FRED API
and exports them as Palantir-ready CSVs.

API Key: Free at https://fred.stlouisfed.org/docs/api/api_key.html
Rate Limit: 120 requests/minute
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# National economic indicator series
NATIONAL_SERIES = {
    "GDPC1": {"name": "Real GDP", "frequency": "Quarterly", "unit": "Billions of Chained 2017 Dollars"},
    "CPIAUCSL": {"name": "CPI All Urban Consumers", "frequency": "Monthly", "unit": "Index 1982-84=100"},
    "CPILFESL": {"name": "Core CPI (ex Food & Energy)", "frequency": "Monthly", "unit": "Index 1982-84=100"},
    "UNRATE": {"name": "Unemployment Rate", "frequency": "Monthly", "unit": "Percent"},
    "PAYEMS": {"name": "Total Nonfarm Payroll", "frequency": "Monthly", "unit": "Thousands of Persons"},
    "MANEMP": {"name": "Manufacturing Employment", "frequency": "Monthly", "unit": "Thousands of Persons"},
    "FEDFUNDS": {"name": "Federal Funds Rate", "frequency": "Monthly", "unit": "Percent"},
    "PCEPI": {"name": "PCE Price Index", "frequency": "Monthly", "unit": "Index 2017=100"},
    "INDPRO": {"name": "Industrial Production Index", "frequency": "Monthly", "unit": "Index 2017=100"},
    "RSAFS": {"name": "Retail Sales", "frequency": "Monthly", "unit": "Millions of Dollars"},
}

# State abbreviation to FRED series prefix mapping
# FRED uses state abbreviations for state-level series
US_STATES = {
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

# State-level series patterns (append state abbreviation)
STATE_SERIES_PATTERNS = {
    "UR": {"name": "Unemployment Rate", "unit": "Percent"},
    "NA": {"name": "Total Nonfarm Employment", "unit": "Thousands of Persons"},
    "NGSP": {"name": "Gross State Product (Nominal)", "unit": "Millions of Dollars"},
}


class FREDCollector:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FRED_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FRED API key required. Get one free at: "
                "https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        self.session = requests.Session()
        self._request_count = 0
        self._last_request_time = 0

    def _throttle(self):
        """Respect FRED's 120 requests/minute rate limit."""
        self._request_count += 1
        if self._request_count % 100 == 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < 60:
                time.sleep(60 - elapsed)
            self._last_request_time = time.time()
            self._request_count = 0

    def fetch_series(
        self,
        series_id: str,
        start_date: str = "2010-01-01",
        end_date: str = "2025-12-31",
    ) -> pd.DataFrame:
        """Fetch a single FRED series and return as DataFrame."""
        self._throttle()
        url = f"{FRED_BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
        }
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "observations" not in data:
            print(f"  Warning: No data for {series_id}")
            return pd.DataFrame()

        df = pd.DataFrame(data["observations"])
        df = df[["date", "value"]].copy()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=["value"])
        return df

    def collect_national(
        self,
        output_dir: str = "sample_data",
        start_date: str = "2010-01-01",
    ) -> pd.DataFrame:
        """Collect all national economic indicators into a single CSV."""
        print("Collecting national economic indicators from FRED...")
        all_data = []

        for series_id, meta in NATIONAL_SERIES.items():
            print(f"  Fetching {meta['name']} ({series_id})...")
            df = self.fetch_series(series_id, start_date=start_date)
            if not df.empty:
                df["series_id"] = series_id
                df["indicator_name"] = meta["name"]
                df["frequency"] = meta["frequency"]
                df["unit"] = meta["unit"]
                df["geography"] = "United States"
                df["geo_level"] = "National"
                all_data.append(df)

        if not all_data:
            print("  No data collected.")
            return pd.DataFrame()

        combined = pd.concat(all_data, ignore_index=True)
        output_path = Path(output_dir) / "fred_national_indicators.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(output_path, index=False)
        print(f"  Saved {len(combined)} records to {output_path}")
        return combined

    def collect_state(
        self,
        states: list[str] = None,
        output_dir: str = "sample_data",
        start_date: str = "2010-01-01",
    ) -> pd.DataFrame:
        """Collect state-level indicators for specified states."""
        if states is None:
            states = list(US_STATES.keys())

        print(f"Collecting state-level indicators for {len(states)} states...")
        all_data = []

        for state in states:
            state = state.upper()
            state_name = US_STATES.get(state, state)
            for suffix, meta in STATE_SERIES_PATTERNS.items():
                series_id = f"{state}{suffix}"
                print(f"  Fetching {state_name} - {meta['name']} ({series_id})...")
                df = self.fetch_series(series_id, start_date=start_date)
                if not df.empty:
                    df["series_id"] = series_id
                    df["indicator_name"] = meta["name"]
                    df["unit"] = meta["unit"]
                    df["geography"] = state_name
                    df["state_code"] = state
                    df["geo_level"] = "State"
                    all_data.append(df)

        if not all_data:
            print("  No state data collected.")
            return pd.DataFrame()

        combined = pd.concat(all_data, ignore_index=True)
        output_path = Path(output_dir) / "fred_state_indicators.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(output_path, index=False)
        print(f"  Saved {len(combined)} records to {output_path}")
        return combined


def main():
    """CLI entry point - collect FRED data."""
    import argparse

    parser = argparse.ArgumentParser(description="Collect FRED economic data")
    parser.add_argument("--output-dir", default="sample_data", help="Output directory")
    parser.add_argument("--start-date", default="2010-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument(
        "--states",
        nargs="*",
        default=None,
        help="State codes to collect (e.g., ID TX CA). Omit for all states.",
    )
    parser.add_argument(
        "--national-only",
        action="store_true",
        help="Only collect national indicators",
    )
    args = parser.parse_args()

    collector = FREDCollector()
    collector.collect_national(output_dir=args.output_dir, start_date=args.start_date)

    if not args.national_only:
        collector.collect_state(
            states=args.states, output_dir=args.output_dir, start_date=args.start_date
        )


if __name__ == "__main__":
    main()
