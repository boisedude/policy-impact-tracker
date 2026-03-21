"""
Congress.gov API Data Collector

Pulls bills filtered by economic policy areas, extracts signing dates
and key metadata, and builds a policy timeline CSV for correlating
with economic indicators.

API Key: Free at https://api.congress.gov/sign-up/
Rate Limit: 5,000 requests/hour
"""

import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CONGRESS_API_BASE = "https://api.congress.gov/v3"

# Policy areas relevant to economic analysis
ECONOMIC_POLICY_AREAS = [
    "Economics and Public Finance",
    "Foreign Trade and International Finance",
    "Taxation",
    "Labor and Employment",
    "Commerce",
    "Finance and Financial Sector",
    "Science, Technology, Communications",
    "Energy",
    "Transportation and Public Works",
    "Agriculture and Food",
]

# Major economic bills to include as landmarks (manually curated)
# These are the ones Hudson would reference in a Senate briefing
LANDMARK_BILLS = [
    {
        "congress": 117,
        "bill_type": "hr",
        "bill_number": 5376,
        "short_name": "Inflation Reduction Act",
        "signed_date": "2022-08-16",
        "policy_area": "Economics and Public Finance",
        "summary": "Climate, energy, healthcare spending; minimum corporate tax; IRS funding",
    },
    {
        "congress": 117,
        "bill_type": "hr",
        "bill_number": 4346,
        "short_name": "CHIPS and Science Act",
        "signed_date": "2022-08-09",
        "policy_area": "Science, Technology, Communications",
        "summary": "Semiconductor manufacturing subsidies; R&D investment; supply chain security",
    },
    {
        "congress": 117,
        "bill_type": "hr",
        "bill_number": 3684,
        "short_name": "Infrastructure Investment and Jobs Act",
        "signed_date": "2021-11-15",
        "policy_area": "Transportation and Public Works",
        "summary": "$1.2T infrastructure: roads, bridges, broadband, water, transit",
    },
    {
        "congress": 117,
        "bill_type": "hr",
        "bill_number": 1319,
        "short_name": "American Rescue Plan Act",
        "signed_date": "2021-03-11",
        "policy_area": "Economics and Public Finance",
        "summary": "$1.9T COVID relief: stimulus checks, unemployment, state/local aid",
    },
    {
        "congress": 116,
        "bill_type": "hr",
        "bill_number": 748,
        "short_name": "CARES Act",
        "signed_date": "2020-03-27",
        "policy_area": "Economics and Public Finance",
        "summary": "$2.2T COVID relief: PPP, stimulus checks, unemployment expansion",
    },
    {
        "congress": 115,
        "bill_type": "hr",
        "bill_number": 1,
        "short_name": "Tax Cuts and Jobs Act",
        "signed_date": "2017-12-22",
        "policy_area": "Taxation",
        "summary": "Corporate tax cut 35%→21%; individual bracket changes; SALT cap",
    },
    {
        "congress": 118,
        "bill_type": "hr",
        "bill_number": 2670,
        "short_name": "National Defense Authorization Act FY2024",
        "signed_date": "2023-12-22",
        "policy_area": "Armed Forces and National Security",
        "summary": "$886B defense authorization; pay raise; procurement reform",
    },
]


class CongressCollector:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CONGRESS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Congress.gov API key required. Get one free at: "
                "https://api.congress.gov/sign-up/"
            )
        self.session = requests.Session()

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make a Congress.gov API request."""
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        params["format"] = "json"

        url = f"{CONGRESS_API_BASE}/{endpoint}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def fetch_enacted_bills(
        self,
        congress: int,
        policy_area: str = None,
        limit: int = 250,
    ) -> list[dict]:
        """Fetch bills that became law in a given Congress, optionally filtered by policy area."""
        bills = []
        offset = 0

        while True:
            params = {"limit": min(limit - len(bills), 250), "offset": offset}
            endpoint = f"bill/{congress}"
            data = self._get(endpoint, params)

            batch = data.get("bills", [])
            if not batch:
                break

            for bill in batch:
                # Check if bill has a latest action indicating it became law
                latest = bill.get("latestAction", {})
                action_text = latest.get("text", "").lower()
                if "became public law" in action_text or "signed by president" in action_text:
                    if policy_area is None or bill.get("policyArea", {}).get("name") == policy_area:
                        bills.append(bill)

            offset += len(batch)
            if len(bills) >= limit or len(batch) < 250:
                break
            time.sleep(0.2)

        return bills

    def get_bill_details(self, congress: int, bill_type: str, bill_number: int) -> dict:
        """Get detailed info for a specific bill including actions."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}"
        data = self._get(endpoint)
        return data.get("bill", {})

    def get_bill_actions(self, congress: int, bill_type: str, bill_number: int) -> list[dict]:
        """Get all actions for a bill to find the signing date."""
        endpoint = f"bill/{congress}/{bill_type}/{bill_number}/actions"
        data = self._get(endpoint)
        return data.get("actions", [])

    def find_signing_date(self, actions: list[dict]) -> str | None:
        """Extract the presidential signing date from bill actions."""
        for action in actions:
            text = action.get("text", "").lower()
            if "became public law" in text or "signed by president" in text:
                return action.get("actionDate")
        return None

    def collect_policy_timeline(
        self,
        congresses: list[int] = None,
        output_dir: str = "sample_data",
    ) -> pd.DataFrame:
        """Build a comprehensive policy timeline from enacted bills."""
        if congresses is None:
            congresses = [115, 116, 117, 118]

        print("Building policy timeline from Congress.gov...")
        all_bills = []

        # Start with curated landmark bills
        print("  Adding landmark economic bills...")
        for bill in LANDMARK_BILLS:
            all_bills.append({
                "congress": bill["congress"],
                "bill_type": bill["bill_type"],
                "bill_number": bill["bill_number"],
                "title": bill["short_name"],
                "short_name": bill["short_name"],
                "signed_date": bill["signed_date"],
                "policy_area": bill["policy_area"],
                "summary": bill["summary"],
                "is_landmark": True,
            })

        # Then fetch enacted bills from the API for each Congress
        for congress in congresses:
            print(f"  Scanning Congress {congress} for enacted bills...")
            for policy_area in ECONOMIC_POLICY_AREAS:
                try:
                    bills = self.fetch_enacted_bills(
                        congress=congress, policy_area=policy_area, limit=50
                    )
                    for bill in bills:
                        bill_type = bill.get("type", "").lower()
                        bill_number = bill.get("number")

                        # Skip if already in landmarks
                        is_dup = any(
                            lb["congress"] == congress
                            and lb["bill_number"] == bill_number
                            for lb in LANDMARK_BILLS
                        )
                        if is_dup:
                            continue

                        # Get signing date from latest action
                        latest = bill.get("latestAction", {})
                        signed_date = latest.get("actionDate")

                        all_bills.append({
                            "congress": congress,
                            "bill_type": bill_type,
                            "bill_number": bill_number,
                            "title": bill.get("title", ""),
                            "short_name": bill.get("title", "")[:100],
                            "signed_date": signed_date,
                            "policy_area": policy_area,
                            "summary": "",
                            "is_landmark": False,
                        })
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    Warning: Error fetching {policy_area}: {e}")

        if not all_bills:
            print("  No bills collected.")
            return pd.DataFrame()

        df = pd.DataFrame(all_bills)
        df["signed_date"] = pd.to_datetime(df["signed_date"], errors="coerce")
        df = df.sort_values("signed_date").reset_index(drop=True)

        output_path = Path(output_dir) / "policy_timeline.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"  Saved {len(df)} bills to {output_path}")
        return df

    def collect_landmark_only(self, output_dir: str = "sample_data") -> pd.DataFrame:
        """Export just the curated landmark bills (no API key needed)."""
        print("Exporting curated landmark economic bills...")
        df = pd.DataFrame(LANDMARK_BILLS)
        df["signed_date"] = pd.to_datetime(df["signed_date"])
        df["is_landmark"] = True

        output_path = Path(output_dir) / "policy_timeline.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"  Saved {len(df)} landmark bills to {output_path}")
        return df


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Collect Congress.gov policy timeline")
    parser.add_argument("--output-dir", default="sample_data")
    parser.add_argument(
        "--landmark-only",
        action="store_true",
        help="Only export curated landmark bills (no API call needed)",
    )
    parser.add_argument(
        "--congresses",
        nargs="*",
        type=int,
        default=[115, 116, 117, 118],
        help="Congress numbers to scan (e.g., 117 118)",
    )
    args = parser.parse_args()

    if args.landmark_only:
        collector = CongressCollector.__new__(CongressCollector)
        collector.collect_landmark_only(output_dir=args.output_dir)
    else:
        collector = CongressCollector()
        collector.collect_policy_timeline(
            congresses=args.congresses, output_dir=args.output_dir
        )


if __name__ == "__main__":
    main()
