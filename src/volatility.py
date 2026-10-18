"""Step 2 - Log returns and rolling annualised volatility.

    r_t       = ln(P_t / P_{t-1})
    sigma_20  = StdDev(r_{t-19}, ..., r_t) * sqrt(252)

pandas' .std() uses the sample standard deviation (ddof=1), which is the same
as Excel's STDEV.S - this is what makes the replication exact.
"""
import numpy as np
import pandas as pd

from src.config import ROLLING_WINDOW, TRADING_DAYS


def add_log_returns(df: pd.DataFrame, price_col: str = "usdkrw_adj") -> pd.DataFrame:
    """Add daily log returns: ln(P_t) - ln(P_{t-1})."""
    out = df.copy()
    out["log_return"] = np.log(out[price_col]).diff()
    return out


def add_rolling_volatility(
    df: pd.DataFrame,
    window: int = ROLLING_WINDOW,
    trading_days: int = TRADING_DAYS,
) -> pd.DataFrame:
    """Add the daily rolling std and its annualised version.

    min_periods=window means the first value only appears once a full
    20-return window exists - exactly like dragging the Excel formula down.
    """
    out = df.copy()
    out["rolling_vol"] = out["log_return"].rolling(window, min_periods=window).std(ddof=1)
    out["annualised_vol"] = out["rolling_vol"] * np.sqrt(trading_days)
    return out
