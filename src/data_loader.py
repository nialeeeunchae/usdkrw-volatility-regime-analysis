"""Step 1 - Data collection and cleaning.

Reads the FRED DEXKOUS series (South Korean won per 1 US dollar, daily noon
buying rates in New York) and handles missing days the same way the Excel
model did: a missing quote is filled with the previous day's rate.
"""
from pathlib import Path

import pandas as pd


def load_fred_usdkrw(path: Path, sheet_name: str = "Daily") -> pd.DataFrame:
    """Load DEXKOUS from the FRED Excel download.

    Returns a DataFrame indexed by date with two columns:
        usdkrw      - raw FRED quote (NaN on US holidays)
        usdkrw_adj  - quote with missing values forward-filled
    """
    df = pd.read_excel(path, sheet_name=sheet_name)
    df = df.rename(columns={"observation_date": "date", "DEXKOUS": "usdkrw"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")

    # FRED leaves US market holidays blank. The Excel model carried the last
    # available rate forward, which makes that day's return exactly zero.
    df["usdkrw_adj"] = df["usdkrw"].ffill()
    return df


def describe_missing(df: pd.DataFrame) -> pd.Series:
    """List the dates that had no FRED quote (useful for the README)."""
    return df.loc[df["usdkrw"].isna(), "usdkrw_adj"]
