"""Step 4 - Validate the Python results against the original Excel model.

The Excel model was exported to CSV (data/excel_output/FX_Volatility.csv).
Columns 0-7 hold the daily calculations; columns 8-10 hold the thresholds and
the summary block (regime day counts, peak date, number of switches).
"""
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# Excel stores ~9 significant digits, so differences below this are rounding.
TOLERANCE = 1e-8


def load_excel_output(path: Path) -> tuple[pd.DataFrame, dict]:
    """Read the Excel export into (daily DataFrame, summary dict)."""
    raw = pd.read_csv(path, header=None, dtype=str)

    # ---- daily block -------------------------------------------------------
    daily = raw.iloc[1:, :8].copy()
    daily.columns = [
        "date", "usdkrw", "usdkrw_adj", "log_return",
        "rolling_vol", "annualised_vol", "regime", "switch",
    ]
    daily = daily.dropna(subset=["date"])
    daily["date"] = pd.to_datetime(daily["date"], format="%d/%m/%Y")
    numeric = ["usdkrw", "usdkrw_adj", "log_return", "rolling_vol", "annualised_vol", "switch"]
    daily[numeric] = daily[numeric].apply(pd.to_numeric, errors="coerce")
    daily = daily.set_index("date")

    # ---- summary block -----------------------------------------------------
    labels = dict(zip(raw[9].str.strip(), raw[10]))
    summary = {
        "lower_threshold": float(raw.iloc[0, 8]),
        "upper_threshold": float(raw.iloc[1, 8]),
        "Stable": int(labels["Stable days"]),
        "Watch": int(labels["Watch days"]),
        "Stress": int(labels["Stress days"]),
        "switches": int(labels["Regime switches"]),
        "peak_date": pd.to_datetime(labels["Peak vol date"], format="%d/%m/%y"),
    }
    return daily, summary


@dataclass
class ValidationReport:
    checks: list = field(default_factory=list)

    def add(self, name: str, python_value, excel_value, passed: bool) -> None:
        self.checks.append((name, python_value, excel_value, passed))

    @property
    def all_passed(self) -> bool:
        return all(c[3] for c in self.checks)

    def to_text(self) -> str:
        lines = [f"{'Check':<38}{'Python':>22}{'Excel':>22}  Result", "-" * 92]
        for name, py, xl, ok in self.checks:
            lines.append(f"{name:<38}{str(py):>22}{str(xl):>22}  {'PASS' if ok else 'FAIL'}")
        lines.append("-" * 92)
        lines.append("ALL CHECKS PASSED" if self.all_passed else "SOME CHECKS FAILED")
        return "\n".join(lines)


def _max_abs_diff(a: pd.Series, b: pd.Series) -> float:
    joined = pd.concat([a, b], axis=1, join="inner").dropna()
    return float(np.abs(joined.iloc[:, 0] - joined.iloc[:, 1]).max())


def validate(py: pd.DataFrame, thresholds: tuple[float, float], excel_path: Path) -> ValidationReport:
    """Compare every stage of the Python pipeline with the Excel numbers."""
    xl, xl_summary = load_excel_output(excel_path)
    report = ValidationReport()

    # 1. Same dates and same number of volatility observations
    n_py = int(py["annualised_vol"].notna().sum())
    n_xl = int(xl["annualised_vol"].notna().sum())
    report.add("Volatility observations", n_py, n_xl, n_py == n_xl)

    # 2. Daily calculations, row by row
    for col in ["usdkrw_adj", "log_return", "rolling_vol", "annualised_vol"]:
        diff = _max_abs_diff(py[col], xl[col])
        tol = 1e-6 if col == "usdkrw_adj" else TOLERANCE
        report.add(f"Max abs diff: {col}", f"{diff:.2e}", "-", diff < tol)

    # 3. Thresholds (50th / 80th percentile)
    for name, py_val, xl_val in [
        ("P50 threshold", thresholds[0], xl_summary["lower_threshold"]),
        ("P80 threshold", thresholds[1], xl_summary["upper_threshold"]),
    ]:
        report.add(name, f"{py_val:.9f}", f"{xl_val:.9f}", abs(py_val - xl_val) < TOLERANCE)

    # 4. Regime labels, row by row
    both = pd.concat([py["regime"], xl["regime"]], axis=1, join="inner", keys=["py", "xl"]).dropna()
    mismatches = int((both["py"] != both["xl"]).sum())
    report.add("Regime label mismatches", mismatches, 0, mismatches == 0)

    # 5. Summary statistics
    counts = py["regime"].value_counts()
    for regime in ["Stable", "Watch", "Stress"]:
        report.add(f"{regime} days", int(counts.get(regime, 0)), xl_summary[regime],
                   int(counts.get(regime, 0)) == xl_summary[regime])

    switches = int(py["switch"].sum())
    report.add("Regime switches", switches, xl_summary["switches"], switches == xl_summary["switches"])

    peak_date = py["annualised_vol"].idxmax()
    report.add("Peak volatility date", peak_date.date(), xl_summary["peak_date"].date(),
               peak_date == xl_summary["peak_date"])

    return report
