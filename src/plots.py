"""Phase 2 - Visualisation with Matplotlib.

Three figures for the README:
    1. USD/KRW rate with the volatility regime shaded behind it
    2. 20-day annualised volatility with the P50 / P80 thresholds
    3. Number of days spent in each regime
"""
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from src.config import (
    GRID_COLOUR, LINE_COLOUR, REGIME_COLOURS, REGIMES, TEXT_PRIMARY, TEXT_SECONDARY,
)


def _style_axes(ax: plt.Axes) -> None:
    """Quiet axes so the data stands out."""
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(GRID_COLOUR)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID_COLOUR, linewidth=0.8)
    ax.set_axisbelow(True)


def _date_axis(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))


def _shade_regimes(ax: plt.Axes, episodes: pd.DataFrame, alpha: float = 0.18) -> None:
    """Draw one coloured band per regime episode.

    Each band runs until the next episode starts, so weekends and holidays
    between two episodes don't leave white gaps.
    """
    ends = list(episodes["start"].iloc[1:]) + [episodes["end"].iloc[-1] + pd.Timedelta(days=1)]
    for regime, start, end in zip(episodes["regime"], episodes["start"], ends):
        ax.axvspan(start, end, color=REGIME_COLOURS[regime], alpha=alpha, linewidth=0)


def _regime_legend(ax: plt.Axes, alpha: float = 0.35) -> None:
    handles = [Patch(color=REGIME_COLOURS[r], alpha=alpha, label=r) for r in REGIMES]
    ax.legend(handles=handles, loc="upper left", frameon=False, ncol=3, fontsize=9,
              labelcolor=TEXT_PRIMARY)


def _title(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(0.06, 0.95, title, fontsize=13, fontweight="bold", color=TEXT_PRIMARY, ha="left")
    fig.text(0.06, 0.905, subtitle, fontsize=9.5, color=TEXT_SECONDARY, ha="left")


def plot_price_with_regimes(df: pd.DataFrame, episodes: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    fig.subplots_adjust(top=0.84, left=0.06, right=0.98, bottom=0.1)
    _shade_regimes(ax, episodes)
    ax.plot(df.index, df["usdkrw_adj"], color=LINE_COLOUR, linewidth=1.6)
    _style_axes(ax)
    _date_axis(ax)
    ax.set_ylabel("KRW per USD", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlim(df.index.min(), df.index.max())
    _regime_legend(ax)
    _title(fig, "USD/KRW exchange rate and volatility regime",
           "Background shows the regime of 20-day annualised volatility · FRED DEXKOUS")
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_volatility(df: pd.DataFrame, thresholds: tuple[float, float],
                    episodes: pd.DataFrame, path: Path) -> None:
    lower, upper = thresholds
    vol_pct = df["annualised_vol"] * 100

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.subplots_adjust(top=0.84, left=0.06, right=0.9, bottom=0.1)
    _shade_regimes(ax, episodes, alpha=0.12)
    ax.plot(vol_pct.index, vol_pct, color=LINE_COLOUR, linewidth=1.6)

    # Threshold lines, labelled directly at the right edge
    for value, label in [(lower, "P50"), (upper, "P80")]:
        ax.axhline(value * 100, color=TEXT_SECONDARY, linewidth=1, linestyle="--")
        ax.annotate(f"{label}  {value * 100:.2f}%", xy=(1.0, value * 100),
                    xycoords=("axes fraction", "data"), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9, color=TEXT_SECONDARY)

    # Mark the peak
    peak_date = vol_pct.idxmax()
    ax.scatter([peak_date], [vol_pct.max()], s=40, color=LINE_COLOUR, zorder=3,
               edgecolor="white", linewidth=1.5)
    ax.annotate(f"Peak {vol_pct.max():.2f}%\n{peak_date:%d %b %Y}", xy=(peak_date, vol_pct.max()),
                xytext=(10, -4), textcoords="offset points", fontsize=9, color=TEXT_PRIMARY, va="top")

    _style_axes(ax)
    _date_axis(ax)
    ax.set_ylabel("Annualised volatility (%)", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlim(vol_pct.dropna().index.min(), vol_pct.index.max())
    ax.set_ylim(bottom=0)
    _regime_legend(ax)
    _title(fig, "USD/KRW 20-day annualised volatility",
           "Stable < P50 ≤ Watch < P80 ≤ Stress · thresholds from the full sample")
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_regime_days(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.6))
    fig.subplots_adjust(top=0.8, left=0.14, right=0.95, bottom=0.12)
    bars = ax.barh(summary.index, summary["days"], height=0.55,
                   color=[REGIME_COLOURS[r] for r in summary.index])
    for bar, (days, share) in zip(bars, summary[["days", "share_pct"]].itertuples(index=False)):
        ax.text(bar.get_width() + 6, bar.get_y() + bar.get_height() / 2,
                f"{days} days ({share:.1f}%)", va="center", fontsize=9, color=TEXT_PRIMARY)
    ax.invert_yaxis()
    _style_axes(ax)
    ax.grid(False)
    ax.tick_params(axis="y", labelsize=10, labelcolor=TEXT_PRIMARY)
    ax.set_xlim(0, summary["days"].max() * 1.3)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    _title(fig, "Days in each regime", f"{int(summary['days'].sum())} trading days with a full 20-day window")
    fig.savefig(path, dpi=200)
    plt.close(fig)
