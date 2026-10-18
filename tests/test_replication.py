"""Automated checks that the Python model reproduces the Excel model.

Run in PyCharm (right-click the tests folder -> Run 'pytest in tests')
or from a terminal:  pytest
"""
import pandas as pd
import pytest

from src import config
from src.data_loader import load_fred_usdkrw
from src.regimes import classify_regimes, compute_thresholds, flag_switches
from src.validation import validate
from src.volatility import add_log_returns, add_rolling_volatility


@pytest.fixture(scope="module")
def model():
    df = add_rolling_volatility(add_log_returns(load_fred_usdkrw(config.RAW_DATA_PATH)))
    thresholds = compute_thresholds(df["annualised_vol"])
    df["regime"] = classify_regimes(df["annualised_vol"], *thresholds)
    df["switch"] = flag_switches(df["regime"])
    return df, thresholds


def test_observation_count(model):
    df, _ = model
    assert df["annualised_vol"].notna().sum() == 891


def test_regime_counts(model):
    df, _ = model
    assert df["regime"].value_counts().to_dict() == {"Stable": 445, "Watch": 267, "Stress": 179}


def test_switches(model):
    df, _ = model
    assert df["switch"].sum() == 67


def test_peak(model):
    df, _ = model
    assert df["annualised_vol"].idxmax() == pd.Timestamp("2025-05-27")
    assert df["annualised_vol"].max() == pytest.approx(0.172347121, abs=1e-8)


def test_full_validation_passes(model):
    df, thresholds = model
    report = validate(df, thresholds, config.EXCEL_OUTPUT_PATH)
    assert report.all_passed, report.to_text()
