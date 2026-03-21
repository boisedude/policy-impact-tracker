"""
Generate realistic sample datasets without requiring API keys.

This creates CSV files that mirror what the real API collectors produce,
using realistic economic data patterns. Hudson can use these to:
1. Immediately start building in Palantir AIP without waiting for API keys
2. Test the demo app locally
3. Upload directly to Palantir Foundry DevTier
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)
OUTPUT_DIR = Path("sample_data")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_monthly_dates(start: str = "2017-01-01", end: str = "2025-12-01") -> pd.DatetimeIndex:
    return pd.date_range(start=start, end=end, freq="MS")


def add_noise(series: pd.Series, scale: float = 0.005) -> pd.Series:
    noise = np.random.normal(0, scale, len(series))
    return series * (1 + noise)


def generate_national_indicators():
    """Generate national economic indicator time series."""
    print("Generating national economic indicators...")
    dates = generate_monthly_dates()
    records = []

    # GDP (quarterly, so we'll generate quarterly dates)
    gdp_dates = pd.date_range("2017-01-01", "2025-10-01", freq="QS")
    gdp_base = 18000  # billions
    gdp_values = []
    val = gdp_base
    for i, d in enumerate(gdp_dates):
        # COVID dip in Q2 2020
        if d.year == 2020 and d.quarter == 2:
            val *= 0.91
        elif d.year == 2020 and d.quarter == 3:
            val *= 1.08
        else:
            val *= 1 + np.random.normal(0.005, 0.003)
        gdp_values.append(val)

    for d, v in zip(gdp_dates, add_noise(pd.Series(gdp_values), 0.001)):
        records.append({
            "date": d, "value": round(v, 1), "series_id": "GDPC1",
            "indicator_name": "Real GDP", "frequency": "Quarterly",
            "unit": "Billions of Chained 2017 Dollars",
            "geography": "United States", "geo_level": "National",
        })

    # CPI - trending up, accelerating 2021-2022
    cpi_base = 243.6
    cpi_values = []
    val = cpi_base
    for d in dates:
        if d.year <= 2020:
            val *= 1 + np.random.normal(0.0015, 0.0005)
        elif d.year == 2021:
            val *= 1 + np.random.normal(0.004, 0.001)
        elif d.year == 2022:
            val *= 1 + np.random.normal(0.006, 0.002)
        elif d.year == 2023:
            val *= 1 + np.random.normal(0.003, 0.001)
        else:
            val *= 1 + np.random.normal(0.002, 0.0008)
        cpi_values.append(val)

    for d, v in zip(dates, cpi_values):
        records.append({
            "date": d, "value": round(v, 1), "series_id": "CPIAUCSL",
            "indicator_name": "CPI All Urban Consumers", "frequency": "Monthly",
            "unit": "Index 1982-84=100",
            "geography": "United States", "geo_level": "National",
        })

    # Unemployment rate
    unemp_values = []
    val = 4.4  # Jan 2017
    for d in dates:
        if d.year < 2020:
            val = max(3.4, val + np.random.normal(-0.03, 0.1))
        elif d.year == 2020 and d.month <= 4:
            val = min(14.7, val + np.random.normal(3.0, 1.0))
        elif d.year == 2020:
            val = max(6.5, val + np.random.normal(-0.5, 0.2))
        elif d.year == 2021:
            val = max(3.8, val + np.random.normal(-0.15, 0.1))
        elif d.year == 2022:
            val = max(3.4, val + np.random.normal(-0.05, 0.08))
        else:
            val = max(3.5, min(4.5, val + np.random.normal(0.02, 0.08)))
        unemp_values.append(val)

    for d, v in zip(dates, unemp_values):
        records.append({
            "date": d, "value": round(v, 1), "series_id": "UNRATE",
            "indicator_name": "Unemployment Rate", "frequency": "Monthly",
            "unit": "Percent",
            "geography": "United States", "geo_level": "National",
        })

    # Nonfarm payroll
    payroll_values = []
    val = 145000  # thousands
    for d in dates:
        if d.year == 2020 and d.month == 3:
            val -= 1400
        elif d.year == 2020 and d.month == 4:
            val -= 20500
        elif d.year == 2020 and d.month >= 5:
            val += np.random.normal(2500, 800)
        elif d.year == 2021:
            val += np.random.normal(500, 200)
        else:
            val += np.random.normal(180, 80)
        payroll_values.append(val)

    for d, v in zip(dates, payroll_values):
        records.append({
            "date": d, "value": round(v, 0), "series_id": "PAYEMS",
            "indicator_name": "Total Nonfarm Payroll", "frequency": "Monthly",
            "unit": "Thousands of Persons",
            "geography": "United States", "geo_level": "National",
        })

    # Manufacturing employment
    mfg_values = []
    val = 12400  # thousands
    for d in dates:
        if d.year == 2020 and d.month == 4:
            val -= 1360
        elif d.year == 2020 and d.month >= 5 and d.month <= 12:
            val += np.random.normal(180, 50)
        elif d.year >= 2022:
            # Post-CHIPS Act modest growth
            val += np.random.normal(8, 15)
        else:
            val += np.random.normal(5, 20)
        mfg_values.append(val)

    for d, v in zip(dates, mfg_values):
        records.append({
            "date": d, "value": round(v, 0), "series_id": "MANEMP",
            "indicator_name": "Manufacturing Employment", "frequency": "Monthly",
            "unit": "Thousands of Persons",
            "geography": "United States", "geo_level": "National",
        })

    # Federal Funds Rate
    ffr_values = []
    val = 0.75
    for d in dates:
        if d.year == 2017:
            val = min(1.5, val + np.random.normal(0.06, 0.02))
        elif d.year == 2018:
            val = min(2.5, val + np.random.normal(0.06, 0.02))
        elif d.year == 2019 and d.month >= 8:
            val = max(1.5, val - np.random.normal(0.08, 0.02))
        elif d.year == 2020 and d.month >= 3:
            val = max(0.05, 0.08)
        elif d.year <= 2021:
            val = max(0.05, 0.08)
        elif d.year == 2022 and d.month >= 3:
            val = min(4.5, val + np.random.normal(0.3, 0.1))
        elif d.year == 2023:
            val = min(5.5, val + np.random.normal(0.08, 0.05))
        elif d.year >= 2024:
            val = max(4.25, val - np.random.normal(0.06, 0.03))
        ffr_values.append(val)

    for d, v in zip(dates, ffr_values):
        records.append({
            "date": d, "value": round(v, 2), "series_id": "FEDFUNDS",
            "indicator_name": "Federal Funds Rate", "frequency": "Monthly",
            "unit": "Percent",
            "geography": "United States", "geo_level": "National",
        })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_DIR / "fred_national_indicators.csv", index=False)
    print(f"  Saved {len(df)} records to fred_national_indicators.csv")
    return df


def generate_state_indicators():
    """Generate state-level economic indicators for select states."""
    print("Generating state-level indicators...")
    dates = generate_monthly_dates()
    records = []

    # Generate for a diverse set of states
    states = {
        "ID": {"name": "Idaho", "base_unemp": 3.8, "base_emp": 750, "growth": 0.003},
        "TX": {"name": "Texas", "base_unemp": 4.3, "base_emp": 12500, "growth": 0.002},
        "CA": {"name": "California", "base_unemp": 5.1, "base_emp": 17000, "growth": 0.001},
        "OH": {"name": "Ohio", "base_unemp": 4.9, "base_emp": 5500, "growth": 0.001},
        "PA": {"name": "Pennsylvania", "base_unemp": 4.8, "base_emp": 6100, "growth": 0.001},
        "AZ": {"name": "Arizona", "base_unemp": 4.8, "base_emp": 2900, "growth": 0.003},
        "MI": {"name": "Michigan", "base_unemp": 4.6, "base_emp": 4400, "growth": 0.001},
        "GA": {"name": "Georgia", "base_unemp": 4.5, "base_emp": 4600, "growth": 0.002},
        "NC": {"name": "North Carolina", "base_unemp": 4.3, "base_emp": 4500, "growth": 0.002},
        "WA": {"name": "Washington", "base_unemp": 4.5, "base_emp": 3400, "growth": 0.002},
    }

    for state_code, info in states.items():
        # Unemployment rate
        val = info["base_unemp"]
        for d in dates:
            if d.year == 2020 and d.month == 4:
                val += np.random.normal(8.0, 2.0)
            elif d.year == 2020 and d.month > 4:
                val = max(info["base_unemp"] + 1, val - np.random.normal(0.4, 0.15))
            elif d.year == 2021:
                val = max(info["base_unemp"], val - np.random.normal(0.1, 0.05))
            else:
                val = max(2.5, min(15, val + np.random.normal(-0.01, 0.1)))
            records.append({
                "date": d, "value": round(val, 1),
                "series_id": f"{state_code}UR",
                "indicator_name": "Unemployment Rate", "unit": "Percent",
                "geography": info["name"], "state_code": state_code,
                "geo_level": "State",
            })

        # Total nonfarm employment
        val = info["base_emp"]
        for d in dates:
            if d.year == 2020 and d.month == 4:
                val *= 0.86
            elif d.year == 2020 and d.month > 4:
                val *= 1 + np.random.normal(0.015, 0.005)
            else:
                val *= 1 + np.random.normal(info["growth"], 0.001)
            records.append({
                "date": d, "value": round(val, 1),
                "series_id": f"{state_code}NA",
                "indicator_name": "Total Nonfarm Employment",
                "unit": "Thousands of Persons",
                "geography": info["name"], "state_code": state_code,
                "geo_level": "State",
            })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_DIR / "fred_state_indicators.csv", index=False)
    print(f"  Saved {len(df)} records to fred_state_indicators.csv")
    return df


def generate_policy_timeline():
    """Generate the policy timeline with real landmark bills."""
    print("Generating policy timeline...")

    bills = [
        {
            "congress": 115, "bill_type": "hr", "bill_number": 1,
            "title": "Tax Cuts and Jobs Act",
            "short_name": "Tax Cuts and Jobs Act",
            "signed_date": "2017-12-22",
            "policy_area": "Taxation",
            "summary": "Corporate tax cut 35%→21%; individual bracket changes; SALT cap $10K; estate tax doubled",
            "is_landmark": True,
            "economic_impact_category": "Tax Policy",
        },
        {
            "congress": 116, "bill_type": "hr", "bill_number": 748,
            "title": "CARES Act",
            "short_name": "CARES Act",
            "signed_date": "2020-03-27",
            "policy_area": "Economics and Public Finance",
            "summary": "$2.2T COVID relief: PPP loans, $1,200 stimulus checks, $600/wk unemployment boost",
            "is_landmark": True,
            "economic_impact_category": "Fiscal Stimulus",
        },
        {
            "congress": 116, "bill_type": "hr", "bill_number": 6201,
            "title": "Families First Coronavirus Response Act",
            "short_name": "Families First Act",
            "signed_date": "2020-03-18",
            "policy_area": "Labor and Employment",
            "summary": "Paid sick leave, free COVID testing, enhanced unemployment, food assistance",
            "is_landmark": True,
            "economic_impact_category": "Labor & Safety Net",
        },
        {
            "congress": 116, "bill_type": "hr", "bill_number": 133,
            "title": "Consolidated Appropriations Act, 2021",
            "short_name": "December 2020 COVID Relief",
            "signed_date": "2020-12-27",
            "policy_area": "Economics and Public Finance",
            "summary": "$900B relief: $600 stimulus checks, PPP extension, $300/wk unemployment",
            "is_landmark": True,
            "economic_impact_category": "Fiscal Stimulus",
        },
        {
            "congress": 117, "bill_type": "hr", "bill_number": 1319,
            "title": "American Rescue Plan Act of 2021",
            "short_name": "American Rescue Plan",
            "signed_date": "2021-03-11",
            "policy_area": "Economics and Public Finance",
            "summary": "$1.9T: $1,400 stimulus checks, enhanced child tax credit, state/local aid, vaccine funding",
            "is_landmark": True,
            "economic_impact_category": "Fiscal Stimulus",
        },
        {
            "congress": 117, "bill_type": "hr", "bill_number": 3684,
            "title": "Infrastructure Investment and Jobs Act",
            "short_name": "Bipartisan Infrastructure Law",
            "signed_date": "2021-11-15",
            "policy_area": "Transportation and Public Works",
            "summary": "$1.2T infrastructure: roads, bridges, broadband, water, EV charging, transit",
            "is_landmark": True,
            "economic_impact_category": "Infrastructure & Investment",
        },
        {
            "congress": 117, "bill_type": "hr", "bill_number": 4346,
            "title": "CHIPS and Science Act",
            "short_name": "CHIPS and Science Act",
            "signed_date": "2022-08-09",
            "policy_area": "Science, Technology, Communications",
            "summary": "$280B: semiconductor manufacturing subsidies, R&D investment, supply chain security",
            "is_landmark": True,
            "economic_impact_category": "Industrial Policy",
        },
        {
            "congress": 117, "bill_type": "hr", "bill_number": 5376,
            "title": "Inflation Reduction Act of 2022",
            "short_name": "Inflation Reduction Act",
            "signed_date": "2022-08-16",
            "policy_area": "Economics and Public Finance",
            "summary": "$738B: clean energy tax credits, Medicare drug negotiation, 15% corporate minimum tax, IRS funding",
            "is_landmark": True,
            "economic_impact_category": "Tax & Energy Policy",
        },
        {
            "congress": 118, "bill_type": "hr", "bill_number": 2670,
            "title": "National Defense Authorization Act for FY2024",
            "short_name": "NDAA FY2024",
            "signed_date": "2023-12-22",
            "policy_area": "Armed Forces and National Security",
            "summary": "$886B defense: 5.2% military pay raise, procurement reform, Indo-Pacific deterrence",
            "is_landmark": True,
            "economic_impact_category": "Defense Spending",
        },
        {
            "congress": 118, "bill_type": "hr", "bill_number": 815,
            "title": "National Security Supplemental",
            "short_name": "Ukraine/Israel/Taiwan Aid",
            "signed_date": "2024-04-24",
            "policy_area": "Foreign Trade and International Finance",
            "summary": "$95B: Ukraine military aid, Israel defense, Indo-Pacific security, TikTok divestiture",
            "is_landmark": True,
            "economic_impact_category": "Foreign Aid & Trade",
        },
    ]

    df = pd.DataFrame(bills)
    df["signed_date"] = pd.to_datetime(df["signed_date"])
    df = df.sort_values("signed_date").reset_index(drop=True)
    df.to_csv(OUTPUT_DIR / "policy_timeline.csv", index=False)
    print(f"  Saved {len(df)} bills to policy_timeline.csv")
    return df


def generate_bls_industry_data():
    """Generate national industry employment breakdown."""
    print("Generating BLS industry employment data...")
    dates = generate_monthly_dates()
    records = []

    industries = {
        "Manufacturing": {"base": 12400, "covid_drop": 0.89, "post_chips_boost": True},
        "Construction": {"base": 7200, "covid_drop": 0.87, "post_chips_boost": True},
        "Information": {"base": 2900, "covid_drop": 0.93, "post_chips_boost": False},
        "Financial Activities": {"base": 8700, "covid_drop": 0.97, "post_chips_boost": False},
        "Professional & Business Services": {"base": 21200, "covid_drop": 0.92, "post_chips_boost": False},
        "Education & Health Services": {"base": 23500, "covid_drop": 0.90, "post_chips_boost": False},
        "Leisure & Hospitality": {"base": 16200, "covid_drop": 0.52, "post_chips_boost": False},
        "Trade, Transport & Utilities": {"base": 27500, "covid_drop": 0.90, "post_chips_boost": False},
        "Mining & Logging": {"base": 710, "covid_drop": 0.88, "post_chips_boost": False},
    }

    for ind_name, info in industries.items():
        val = info["base"]
        for d in dates:
            if d.year == 2020 and d.month == 4:
                val *= info["covid_drop"]
            elif d.year == 2020 and d.month > 4:
                val *= 1 + np.random.normal(0.02, 0.005)
            elif d.year >= 2022 and d.month >= 9 and info["post_chips_boost"]:
                val *= 1 + np.random.normal(0.002, 0.001)
            else:
                val *= 1 + np.random.normal(0.001, 0.001)
            records.append({
                "date": d, "value": round(val, 0),
                "indicator_name": f"{ind_name} Employment",
                "unit": "Thousands", "geography": "United States",
                "geo_level": "National", "source": "BLS CES",
            })

    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_DIR / "bls_national_industry.csv", index=False)
    print(f"  Saved {len(df)} records to bls_national_industry.csv")
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("Generating sample datasets for Economic Policy Impact Tracker")
    print("=" * 60)
    generate_national_indicators()
    generate_state_indicators()
    generate_policy_timeline()
    generate_bls_industry_data()
    print("\nDone! All sample data is in the sample_data/ directory.")
    print("These CSVs are ready for upload to Palantir AIP DevTier.")
