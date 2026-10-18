"""USD/KRW Volatility Regime Analysis - full pipeline.

Run from PyCharm (right-click -> Run 'main') or from a terminal:
    python main.py

Steps
    1. Load FRED DEXKOUS data and forward-fill missing quotes
    2. Compute log returns and 20-day annualised volatility
    3. Classify Stable / Watch / Stress using the 50th / 80th percentiles
    4. Validate every step against the original Excel model
    5. Save tables and charts
"""
import pandas as pd

from src import config
from src.data_loader import describe_missing, load_fred_usdkrw
from src.plots import plot_price_with_regimes, plot_regime_days, plot_volatility
from src.regimes import (
    classify_regimes, compute_thresholds, flag_switches,
    regime_episodes, regime_summary, transition_matrix,
)
from src.validation import validate
from src.volatility import add_log_returns, add_rolling_volatility


def run() -> pd.DataFrame:
    config.FIGURES_DIR.mkdir(exist_ok=True)
    config.OUTPUTS_DIR.mkdir(exist_ok=True)

    # 1. Data --------------------------------------------------------------
    df = load_fred_usdkrw(config.RAW_DATA_PATH)
    missing = describe_missing(df)
    print(f"Loaded {len(df)} trading days: {df.index.min():%d %b %Y} - {df.index.max():%d %b %Y}")
    print(f"Missing FRED quotes forward-filled: {len(missing)}")

    # 2. Volatility --------------------------------------------------------
    df = add_log_returns(df)
    df = add_rolling_volatility(df)

    # 3. Regimes -----------------------------------------------------------
    thresholds = compute_thresholds(df["annualised_vol"])
    df["regime"] = classify_regimes(df["annualised_vol"], *thresholds)
    df["switch"] = flag_switches(df["regime"])

    summary = regime_summary(df)
    episodes = regime_episodes(df["regime"])
    transitions = transition_matrix(df["regime"])

    print(f"\nThresholds: P50 = {thresholds[0]:.4%}, P80 = {thresholds[1]:.4%}")
    print("\nRegime summary")
    print(summary.round(4).to_string())
    print(f"\nRegime switches: {int(df['switch'].sum())}")
    print(f"Peak volatility: {df['annualised_vol'].max():.4%} on {df['annualised_vol'].idxmax():%d %b %Y}")
    print("\nAverage episode length (days)")
    print(episodes.groupby("regime")["days"].agg(["count", "mean", "max"]).reindex(config.REGIMES).round(1).to_string())
    print("\nDaily transition probabilities (row = today, column = tomorrow)")
    print(transitions.round(3).to_string())

    # 4. Validation --------------------------------------------------------
    report = validate(df, thresholds, config.EXCEL_OUTPUT_PATH)
    print("\nValidation against the Excel model")
    print(report.to_text())

    # 5. Save outputs ------------------------------------------------------
    df.to_csv(config.OUTPUTS_DIR / "regime_classification.csv", float_format="%.10f")
    summary.to_csv(config.OUTPUTS_DIR / "regime_summary.csv")
    episodes.to_csv(config.OUTPUTS_DIR / "regime_episodes.csv", index=False)
    transitions.to_csv(config.OUTPUTS_DIR / "transition_matrix.csv")
    (config.OUTPUTS_DIR / "validation_report.txt").write_text(report.to_text(), encoding="utf-8")

    plot_price_with_regimes(df, episodes, config.FIGURES_DIR / "usdkrw_regimes.png")
    plot_volatility(df, thresholds, episodes, config.FIGURES_DIR / "volatility_regimes.png")
    plot_regime_days(summary, config.FIGURES_DIR / "regime_days.png")
    print(f"\nSaved tables to {config.OUTPUTS_DIR} and charts to {config.FIGURES_DIR}")

    return df


if __name__ == "__main__":
    run()
