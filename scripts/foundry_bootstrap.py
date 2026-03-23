#!/usr/bin/env python3
"""
Foundry Bootstrap Script
========================
Pulls real economic data from federal APIs, then uploads it to your
Palantir Foundry DevTier instance as queryable Parquet datasets.

Prerequisites:
  pip install foundry-platform-sdk pandas pyarrow requests python-dotenv

Usage:
  python scripts/foundry_bootstrap.py \
    --foundry-token YOUR_FOUNDRY_TOKEN \
    --foundry-host  YOUR_NAME.usw-XX.palantirfoundry.com \
    --fred-key      YOUR_FRED_API_KEY \
    --space-rid     ri.compass.main.folder.XXXX  (your Space RID)

To find your Space RID, run with --list-spaces first:
  python scripts/foundry_bootstrap.py \
    --foundry-token YOUR_TOKEN \
    --foundry-host  YOUR_HOST \
    --list-spaces
"""

import argparse
import io
import os
import sys
import time

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

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

STATE_SERIES = {
    "UR": {"name": "Unemployment Rate", "unit": "Percent"},
    "NA": {"name": "Total Nonfarm Employment", "unit": "Thousands of Persons"},
}

DEMO_STATES = {
    "ID": "Idaho", "TX": "Texas", "CA": "California", "OH": "Ohio",
    "PA": "Pennsylvania", "AZ": "Arizona", "MI": "Michigan",
    "GA": "Georgia", "NC": "North Carolina", "WA": "Washington",
}

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

NATIONAL_CES = {
    "CES0000000001": {"name": "Total Nonfarm Employment", "unit": "Thousands"},
    "CES3000000001": {"name": "Manufacturing Employment", "unit": "Thousands"},
    "CES1000000001": {"name": "Mining & Logging Employment", "unit": "Thousands"},
    "CES2000000001": {"name": "Construction Employment", "unit": "Thousands"},
    "CES4000000001": {"name": "Trade, Transport & Utilities Employment", "unit": "Thousands"},
    "CES5000000001": {"name": "Information Employment", "unit": "Thousands"},
    "CES5500000001": {"name": "Financial Activities Employment", "unit": "Thousands"},
    "CES6000000001": {"name": "Professional & Business Services Employment", "unit": "Thousands"},
    "CES6500000001": {"name": "Education & Health Services Employment", "unit": "Thousands"},
}

# Curated list of economically significant enacted laws (2017-2025)
POLICY_TIMELINE = [
    # === LANDMARK BILLS ===
    {"congress": 115, "bill_type": "hr", "bill_number": 1, "short_name": "Tax Cuts and Jobs Act",
     "signed_date": "2017-12-22", "policy_area": "Taxation",
     "summary": "Corporate tax cut 35%→21%; individual bracket changes; SALT cap", "is_landmark": True},
    {"congress": 116, "bill_type": "hr", "bill_number": 748, "short_name": "CARES Act",
     "signed_date": "2020-03-27", "policy_area": "Economics and Public Finance",
     "summary": "$2.2T COVID relief: PPP, stimulus checks, unemployment expansion", "is_landmark": True},
    {"congress": 117, "bill_type": "hr", "bill_number": 1319, "short_name": "American Rescue Plan Act",
     "signed_date": "2021-03-11", "policy_area": "Economics and Public Finance",
     "summary": "$1.9T COVID relief: stimulus checks, unemployment, state/local aid", "is_landmark": True},
    {"congress": 117, "bill_type": "hr", "bill_number": 3684, "short_name": "Infrastructure Investment and Jobs Act",
     "signed_date": "2021-11-15", "policy_area": "Transportation and Public Works",
     "summary": "$1.2T infrastructure: roads, bridges, broadband, water, transit", "is_landmark": True},
    {"congress": 117, "bill_type": "hr", "bill_number": 4346, "short_name": "CHIPS and Science Act",
     "signed_date": "2022-08-09", "policy_area": "Science, Technology, Communications",
     "summary": "Semiconductor manufacturing subsidies; R&D investment; supply chain security", "is_landmark": True},
    {"congress": 117, "bill_type": "hr", "bill_number": 5376, "short_name": "Inflation Reduction Act",
     "signed_date": "2022-08-16", "policy_area": "Economics and Public Finance",
     "summary": "Climate, energy, healthcare spending; minimum corporate tax; IRS funding", "is_landmark": True},
    {"congress": 118, "bill_type": "hr", "bill_number": 2670, "short_name": "National Defense Authorization Act FY2024",
     "signed_date": "2023-12-22", "policy_area": "Armed Forces and National Security",
     "summary": "$886B defense authorization; pay raise; procurement reform", "is_landmark": True},
    # === MAJOR APPROPRIATIONS & BUDGETS ===
    {"congress": 115, "bill_type": "hr", "bill_number": 244, "short_name": "Consolidated Appropriations Act, 2017",
     "signed_date": "2017-05-05", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 115, "bill_type": "hr", "bill_number": 1892, "short_name": "Bipartisan Budget Act of 2018",
     "signed_date": "2018-02-09", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 115, "bill_type": "hr", "bill_number": 1625, "short_name": "Consolidated Appropriations Act, 2018",
     "signed_date": "2018-03-23", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 648, "short_name": "Consolidated Appropriations Act, 2019",
     "signed_date": "2019-02-15", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 3877, "short_name": "Bipartisan Budget Act of 2019",
     "signed_date": "2019-08-02", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 1865, "short_name": "Consolidated Appropriations Act, 2020",
     "signed_date": "2019-12-20", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 133, "short_name": "Consolidated Appropriations Act, 2021",
     "signed_date": "2020-12-27", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 117, "bill_type": "hr", "bill_number": 2471, "short_name": "Consolidated Appropriations Act, 2022",
     "signed_date": "2022-03-15", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 117, "bill_type": "hr", "bill_number": 2617, "short_name": "Consolidated Appropriations Act, 2023",
     "signed_date": "2022-12-29", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 118, "bill_type": "hr", "bill_number": 4366, "short_name": "Consolidated Appropriations Act, 2024",
     "signed_date": "2024-03-09", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 118, "bill_type": "hr", "bill_number": 2882, "short_name": "Fiscal Responsibility Act of 2023",
     "signed_date": "2023-06-03", "policy_area": "Economics and Public Finance", "summary": "Debt ceiling deal", "is_landmark": False},
    {"congress": 118, "bill_type": "hr", "bill_number": 10545, "short_name": "American Relief Act, 2025",
     "signed_date": "2024-12-21", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    # === COVID ECONOMIC RESPONSE ===
    {"congress": 116, "bill_type": "hr", "bill_number": 266, "short_name": "Paycheck Protection Program and Health Care Enhancement Act",
     "signed_date": "2020-04-24", "policy_area": "Economics and Public Finance", "summary": "", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 7010, "short_name": "Paycheck Protection Program Flexibility Act of 2020",
     "signed_date": "2020-06-05", "policy_area": "Commerce", "summary": "", "is_landmark": False},
    {"congress": 117, "bill_type": "hr", "bill_number": 1799, "short_name": "PPP Extension Act of 2021",
     "signed_date": "2021-03-30", "policy_area": "Commerce", "summary": "", "is_landmark": False},
    # === TRADE & INTERNATIONAL ===
    {"congress": 116, "bill_type": "hr", "bill_number": 5430, "short_name": "United States-Mexico-Canada Agreement Implementation Act",
     "signed_date": "2020-10-21", "policy_area": "Foreign Trade and International Finance", "summary": "USMCA", "is_landmark": False},
    {"congress": 117, "bill_type": "hr", "bill_number": 7108, "short_name": "Suspending Normal Trade Relations with Russia and Belarus Act",
     "signed_date": "2022-04-08", "policy_area": "Foreign Trade and International Finance", "summary": "", "is_landmark": False},
    {"congress": 117, "bill_type": "hr", "bill_number": 6968, "short_name": "Ending Importation of Russian Oil Act",
     "signed_date": "2022-04-08", "policy_area": "Foreign Trade and International Finance", "summary": "", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 7120, "short_name": "Holding Foreign Companies Accountable Act",
     "signed_date": "2020-12-18", "policy_area": "Finance and Financial Sector", "summary": "", "is_landmark": False},
    {"congress": 118, "bill_type": "hr", "bill_number": 1107, "short_name": "Prohibiting Russian Uranium Imports Act",
     "signed_date": "2024-05-13", "policy_area": "Energy", "summary": "", "is_landmark": False},
    {"congress": 118, "bill_type": "s", "bill_number": 138, "short_name": "United States-Taiwan Initiative on 21st-Century Trade First Agreement Implementation Act",
     "signed_date": "2023-08-07", "policy_area": "Foreign Trade and International Finance", "summary": "", "is_landmark": False},
    # === FINANCIAL REGULATION ===
    {"congress": 115, "bill_type": "s", "bill_number": 2155, "short_name": "Economic Growth, Regulatory Relief, and Consumer Protection Act",
     "signed_date": "2018-05-24", "policy_area": "Finance and Financial Sector", "summary": "Dodd-Frank rollback for community banks", "is_landmark": False},
    {"congress": 116, "bill_type": "hr", "bill_number": 3151, "short_name": "Taxpayer First Act",
     "signed_date": "2019-07-01", "policy_area": "Taxation", "summary": "", "is_landmark": False},
    # === SECTOR IMPACT ===
    {"congress": 115, "bill_type": "hr", "bill_number": 2, "short_name": "Agriculture Improvement Act of 2018",
     "signed_date": "2018-12-20", "policy_area": "Agriculture and Food", "summary": "Farm Bill", "is_landmark": False},
    {"congress": 115, "bill_type": "hr", "bill_number": 302, "short_name": "FAA Reauthorization Act of 2018",
     "signed_date": "2018-10-05", "policy_area": "Transportation and Public Works", "summary": "", "is_landmark": False},
    {"congress": 118, "bill_type": "hr", "bill_number": 3935, "short_name": "FAA Reauthorization Act of 2024",
     "signed_date": "2024-05-16", "policy_area": "Transportation and Public Works", "summary": "", "is_landmark": False},
    {"congress": 117, "bill_type": "s", "bill_number": 3580, "short_name": "Ocean Shipping Reform Act of 2022",
     "signed_date": "2022-06-16", "policy_area": "Transportation and Public Works", "summary": "", "is_landmark": False},
    {"congress": 115, "bill_type": "hr", "bill_number": 6311, "short_name": "National Quantum Initiative Act",
     "signed_date": "2018-12-21", "policy_area": "Science, Technology, Communications", "summary": "", "is_landmark": False},
    # === TAX ===
    {"congress": 118, "bill_type": "hr", "bill_number": 5863, "short_name": "Federal Disaster Tax Relief Act of 2023",
     "signed_date": "2024-12-12", "policy_area": "Taxation", "summary": "", "is_landmark": False},
]


def fetch_fred_series(api_key, series_id, start_date="2010-01-01", retries=3):
    """Fetch a single FRED series with retry logic."""
    for attempt in range(retries):
        try:
            resp = requests.get(f"{FRED_BASE_URL}/series/observations", params={
                "series_id": series_id, "api_key": api_key, "file_type": "json",
                "observation_start": start_date, "observation_end": "2025-12-31",
            }, timeout=30)
            if resp.status_code == 500 and attempt < retries - 1:
                time.sleep(3)
                continue
            resp.raise_for_status()
            data = resp.json()
            if "observations" not in data:
                return pd.DataFrame()
            df = pd.DataFrame(data["observations"])[["date", "value"]].copy()
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])
            return df.dropna(subset=["value"])
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                print(f"    FAILED: {series_id}: {e}")
                return pd.DataFrame()


def collect_fred_national(api_key):
    """Collect all national economic indicators from FRED."""
    print("\n[1/4] Collecting FRED national indicators...")
    all_data = []
    for series_id, meta in NATIONAL_SERIES.items():
        print(f"  {meta['name']} ({series_id})...", end=" ", flush=True)
        time.sleep(0.5)
        df = fetch_fred_series(api_key, series_id)
        if not df.empty:
            df["series_id"] = series_id
            df["indicator_name"] = meta["name"]
            df["frequency"] = meta["frequency"]
            df["unit"] = meta["unit"]
            df["geography"] = "United States"
            df["geo_level"] = "National"
            all_data.append(df)
            print(f"{len(df)} records")
        else:
            print("EMPTY")
    result = pd.concat(all_data, ignore_index=True)
    print(f"  Total: {len(result)} records, {result['indicator_name'].nunique()} indicators")
    return result


def collect_fred_state(api_key):
    """Collect state-level indicators from FRED."""
    print("\n[2/4] Collecting FRED state indicators...")
    all_data = []
    for state, state_name in DEMO_STATES.items():
        for suffix, meta in STATE_SERIES.items():
            sid = f"{state}{suffix}"
            print(f"  {state_name} — {meta['name']} ({sid})...", end=" ", flush=True)
            time.sleep(0.5)
            df = fetch_fred_series(api_key, sid)
            if not df.empty:
                df["series_id"] = sid
                df["indicator_name"] = meta["name"]
                df["unit"] = meta["unit"]
                df["geography"] = state_name
                df["state_code"] = state
                df["geo_level"] = "State"
                all_data.append(df)
                print(f"{len(df)} records")
            else:
                print("EMPTY")
    result = pd.concat(all_data, ignore_index=True)
    print(f"  Total: {len(result)} records, {result['geography'].nunique()} states")
    return result


def collect_bls_industry():
    """Collect national industry employment from BLS (no key needed)."""
    print("\n[3/4] Collecting BLS industry employment...")
    all_data = []
    for decade_start, decade_end in [(2010, 2019), (2020, 2025)]:
        print(f"  {decade_start}-{decade_end}...", end=" ", flush=True)
        resp = requests.post(BLS_API_URL, json={
            "seriesid": list(NATIONAL_CES.keys()),
            "startyear": str(decade_start),
            "endyear": str(decade_end),
        }, timeout=60)
        result = resp.json()
        if result.get("status") != "REQUEST_SUCCEEDED":
            print(f"WARNING: {result.get('message', 'unknown error')}")
            continue
        count = 0
        for series in result.get("Results", {}).get("series", []):
            sid = series["seriesID"]
            meta = NATIONAL_CES[sid]
            for obs in series.get("data", []):
                if obs["period"] == "M13":
                    continue
                all_data.append({
                    "date": pd.Timestamp(year=int(obs["year"]), month=int(obs["period"].replace("M", "")), day=1),
                    "value": float(obs["value"].replace(",", "")),
                    "series_id": sid,
                    "indicator_name": meta["name"],
                    "unit": meta["unit"],
                    "geography": "United States",
                    "geo_level": "National",
                    "source": "BLS CES",
                })
                count += 1
        print(f"{count} records")
        time.sleep(1)
    result = pd.DataFrame(all_data).sort_values("date").reset_index(drop=True)
    print(f"  Total: {len(result)} records, {result['indicator_name'].nunique()} industries")
    return result


def collect_policy_timeline():
    """Return the curated policy timeline (no API call needed)."""
    print("\n[4/4] Building curated policy timeline...")
    df = pd.DataFrame(POLICY_TIMELINE)
    df["signed_date"] = pd.to_datetime(df["signed_date"])
    df["economic_impact_category"] = df["policy_area"]
    df = df.sort_values("signed_date").reset_index(drop=True)
    print(f"  {len(df)} bills ({df['is_landmark'].sum()} landmarks + {(~df['is_landmark']).sum()} additional)")
    return df


# ---------------------------------------------------------------------------
# Foundry upload
# ---------------------------------------------------------------------------

def get_foundry_client(token, hostname):
    """Create a Foundry SDK client."""
    import foundry_sdk as foundry
    return foundry.FoundryClient(
        auth=foundry.UserTokenAuth(token=token),
        hostname=f"https://{hostname}",
    )


def list_spaces(client):
    """List available Foundry spaces."""
    print("\nAvailable Spaces:")
    for space in client.filesystem.Space.list(preview=True):
        print(f"  {space.display_name}")
        print(f"    RID:  {space.rid}")
        print(f"    Path: {space.path}")
        print()


def upload_to_foundry(client, space_rid, dataframes):
    """Create project folder, datasets, and upload data to Foundry."""
    from foundry_sdk.v2.core.models import DatasetSchema, DatasetFieldSchema

    # Create project folder inside the space
    print("\nCreating project folder in Foundry...")
    folder = client.filesystem.Folder.create(
        display_name="Economic Policy Impact Tracker",
        parent_folder_rid=space_rid,
        preview=True,
    )
    print(f"  Created: {folder.path} (RID: {folder.rid})")

    # Dataset definitions: name -> (dataframe, schema fields)
    dataset_defs = {
        "fred_national_indicators": (
            dataframes["national"],
            [("DATE", "date", False), ("DOUBLE", "value", False), ("STRING", "series_id", False),
             ("STRING", "indicator_name", False), ("STRING", "frequency", True),
             ("STRING", "unit", False), ("STRING", "geography", False), ("STRING", "geo_level", False)],
        ),
        "fred_state_indicators": (
            dataframes["state"],
            [("DATE", "date", False), ("DOUBLE", "value", False), ("STRING", "series_id", False),
             ("STRING", "indicator_name", False), ("STRING", "unit", False),
             ("STRING", "geography", False), ("STRING", "state_code", False), ("STRING", "geo_level", False)],
        ),
        "bls_national_industry": (
            dataframes["bls"],
            [("DATE", "date", False), ("DOUBLE", "value", False), ("STRING", "series_id", True),
             ("STRING", "indicator_name", False), ("STRING", "unit", False),
             ("STRING", "geography", False), ("STRING", "geo_level", False), ("STRING", "source", True)],
        ),
        "policy_timeline": (
            dataframes["policy"],
            [("INTEGER", "congress", False), ("STRING", "bill_type", False), ("INTEGER", "bill_number", False),
             ("STRING", "short_name", False), ("DATE", "signed_date", False),
             ("STRING", "policy_area", False), ("STRING", "summary", True),
             ("BOOLEAN", "is_landmark", False), ("STRING", "economic_impact_category", True)],
        ),
    }

    created_datasets = {}

    for name, (df, schema_fields) in dataset_defs.items():
        print(f"\n  Creating dataset '{name}'...")

        # Create dataset
        ds = client.datasets.Dataset.create(name=name, parent_folder_rid=folder.rid)
        print(f"    RID: {ds.rid}")

        # Convert date columns to date objects for Parquet
        df_copy = df.copy()
        for col in df_copy.columns:
            if "date" in col.lower():
                df_copy[col] = pd.to_datetime(df_copy[col]).dt.date

        # Convert to Parquet
        buf = io.BytesIO()
        df_copy.to_parquet(buf, index=False, engine="pyarrow")

        # Upload via transaction
        txn = client.datasets.Dataset.Transaction.create(ds.rid, transaction_type="SNAPSHOT")
        client.datasets.Dataset.File.upload(
            ds.rid, file_path=f"spark/{name}.snappy.parquet",
            body=buf.getvalue(), transaction_rid=txn.rid,
        )
        client.datasets.Dataset.Transaction.commit(ds.rid, transaction_rid=txn.rid)
        print(f"    Uploaded {len(df)} rows as Parquet")

        # Set schema
        schema = DatasetSchema(field_schema_list=[
            DatasetFieldSchema(type=t, name=n, nullable=null) for t, n, null in schema_fields
        ])
        client.datasets.Dataset.put_schema(ds.rid, schema=schema, dataframe_reader="PARQUET")
        print(f"    Schema set ({len(schema_fields)} fields)")

        created_datasets[name] = ds.rid

    return folder.rid, created_datasets


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap the Economic Policy Impact Tracker in Palantir Foundry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--foundry-token", required=True, help="Foundry personal access token")
    parser.add_argument("--foundry-host", required=True,
                        help="Foundry hostname (e.g., myname.usw-18.palantirfoundry.com)")
    parser.add_argument("--fred-key", help="FRED API key (free at fred.stlouisfed.org)")
    parser.add_argument("--space-rid", help="Foundry Space RID to create project in")
    parser.add_argument("--list-spaces", action="store_true", help="List available spaces and exit")
    parser.add_argument("--collect-only", action="store_true", help="Only collect data, don't upload")
    parser.add_argument("--output-dir", default="real_data", help="Directory for collected CSVs")
    args = parser.parse_args()

    # --- List spaces mode ---
    if args.list_spaces:
        client = get_foundry_client(args.foundry_token, args.foundry_host)
        list_spaces(client)
        return

    # --- Validate ---
    if not args.fred_key:
        print("ERROR: --fred-key required. Get one free at https://fred.stlouisfed.org/docs/api/api_key.html")
        sys.exit(1)

    if not args.collect_only and not args.space_rid:
        print("ERROR: --space-rid required for upload. Run with --list-spaces to find yours.")
        sys.exit(1)

    # --- Collect data ---
    print("=" * 60)
    print("ECONOMIC POLICY IMPACT TRACKER — Data Pipeline")
    print("=" * 60)

    national_df = collect_fred_national(args.fred_key)
    state_df = collect_fred_state(args.fred_key)
    bls_df = collect_bls_industry()
    policy_df = collect_policy_timeline()

    # Save CSVs locally
    os.makedirs(args.output_dir, exist_ok=True)
    national_df.to_csv(f"{args.output_dir}/fred_national_indicators.csv", index=False)
    state_df.to_csv(f"{args.output_dir}/fred_state_indicators.csv", index=False)
    bls_df.to_csv(f"{args.output_dir}/bls_national_industry.csv", index=False)
    policy_df.to_csv(f"{args.output_dir}/policy_timeline.csv", index=False)
    print(f"\nCSVs saved to {args.output_dir}/")

    if args.collect_only:
        print("\n--collect-only: Skipping Foundry upload.")
        return

    # --- Upload to Foundry ---
    print("\n" + "=" * 60)
    print("UPLOADING TO FOUNDRY")
    print("=" * 60)

    client = get_foundry_client(args.foundry_token, args.foundry_host)

    dataframes = {
        "national": national_df,
        "state": state_df,
        "bls": bls_df,
        "policy": policy_df,
    }

    folder_rid, dataset_rids = upload_to_foundry(client, args.space_rid, dataframes)

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nProject folder: {folder_rid}")
    print("\nDataset RIDs (save these for Ontology setup):")
    for name, rid in dataset_rids.items():
        print(f"  {name}: {rid}")
    print(f"\nNext step: Open Foundry and build the Ontology.")
    print(f"See docs/AIP_BUILD_GUIDE.md for the walkthrough.")


if __name__ == "__main__":
    main()
