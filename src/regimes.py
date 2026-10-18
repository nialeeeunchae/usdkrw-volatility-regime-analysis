"""Step 3 - Three-regime classification (Stable / Watch / Stress).

Thresholds are the 50th and 80th percentiles of all annualised volatility
observations in the sample:

    Stable : vol <  P50
    Watch  : P50 <= vol < P80
    Stress : vol >= P80

np.percentile's default ("linear") method is the same interpolation as
Excel's PERCENTILE / PERCENTILE.INC.

Note: using the full sample to set thresholds is fine for describing the past,
but it uses information that was not available at each date (look-ahead bias).
"""
import numpy as np
import pandas as pd

from src.config import LOWER_PERCENTILE, REGIMES, UPPER_PERCENTILE


def compute_thresholds(
    vol: pd.Series,
    lower_pct: float = LOWER_PERCENTILE,
    upper_pct: float = UPPER_PERCENTILE,
) -> tuple[float, float]:
    """Return the (lower, upper) volatility thresholds from the full sample."""
    clean = vol.dropna()
    lower, upper = np.percentile(clean, [lower_pct, upper_pct])
    return float(lower), float(upper)


def classify_regimes(vol: pd.Series, lower: float, upper: float) -> pd.Series:
    """Label each observation Stable / Watch / Stress (NaN where vol is NaN)."""
    labels = np.select(
        [vol < lower, vol < upper, vol >= upper],
        REGIMES,
        default="",
    )
    regime = pd.Series(labels, index=vol.index, name="regime")
    return regime.where(vol.notna())


def flag_switches(regime: pd.Series) -> pd.Series:
    """1 if today's regime differs from yesterday's, else 0.

    The first classified day has no previous regime, so it is left as NaN
    (matching the Excel model, where the switch column starts one row later).
    """
    valid = regime.dropna()
    switch = (valid != valid.shift()).astype(float)
    switch.iloc[0] = np.nan
    return switch.reindex(regime.index).rename("switch")


def regime_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Days, share of sample and volatility range for each regime."""
    data = df.dropna(subset=["regime"])
    summary = (
        data.groupby("regime")["annualised_vol"]
        .agg(days="count", min_vol="min", mean_vol="mean", max_vol="max")
        .reindex(REGIMES)
    )
    summary["share_pct"] = summary["days"] / summary["days"].sum() * 100
    return summary[["days", "share_pct", "min_vol", "mean_vol", "max_vol"]]


def regime_episodes(regime: pd.Series) -> pd.DataFrame:
    """Collapse the daily labels into consecutive episodes (spells).

    Each row is one uninterrupted stretch of the same regime, which answers
    questions like "how long does a Stress period usually last?".
    """
    valid = regime.dropna()
    episode_id = (valid != valid.shift()).cumsum()
    episodes = (
        valid.groupby(episode_id)
        .agg(
            regime="first",
            start=lambda s: s.index[0],
            end=lambda s: s.index[-1],
            days="size",
        )
        .reset_index(drop=True)
    )
    return episodes


def transition_matrix(regime: pd.Series) -> pd.DataFrame:
    """Probability of moving from today's regime (rows) to tomorrow's (columns)."""
    valid = regime.dropna()
    pairs = pd.DataFrame({"from": valid.shift().iloc[1:], "to": valid.iloc[1:]})
    counts = pd.crosstab(pairs["from"], pairs["to"]).reindex(index=REGIMES, columns=REGIMES, fill_value=0)
    return counts.div(counts.sum(axis=1), axis=0)
