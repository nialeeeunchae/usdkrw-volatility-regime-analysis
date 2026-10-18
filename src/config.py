"""Project-wide settings: file paths, model parameters and chart colours.

Keeping every "magic number" here means the analysis can be re-run with a
different window or percentile split by editing one file.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (resolved from this file, so the project runs from any working dir)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_PATH = DATA_DIR / "raw" / "DEXKOUS.xlsx"                 # FRED download
EXCEL_OUTPUT_PATH = DATA_DIR / "excel_output" / "FX_Volatility.csv"  # original Excel model
FIGURES_DIR = PROJECT_ROOT / "figures"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# ---------------------------------------------------------------------------
# Model parameters (identical to the original Excel model)
# ---------------------------------------------------------------------------
ROLLING_WINDOW = 20        # trading days in the rolling volatility window
TRADING_DAYS = 252         # annualisation factor
LOWER_PERCENTILE = 50      # Stable / Watch boundary
UPPER_PERCENTILE = 80      # Watch / Stress boundary

REGIMES = ["Stable", "Watch", "Stress"]

# ---------------------------------------------------------------------------
# Chart colours: regimes are *states*, so they use a status palette
# (good / warning / critical) and are always shown with a text label too.
# ---------------------------------------------------------------------------
REGIME_COLOURS = {
    "Stable": "#0ca30c",
    "Watch": "#fab219",
    "Stress": "#d03b3b",
}
LINE_COLOUR = "#2a78d6"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOUR = "#e4e3df"
