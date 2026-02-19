"""
================================================================================
  PREDICTION MARKET ROOKIE ANALYSIS
  ----------------------------------
  A beginner-friendly analysis of 400M+ prediction market trades.
  Generates 8 key visualizations that teach core concepts in:
    - Market calibration & efficiency
    - Behavioral biases (longshot bias)
    - Market microstructure (maker vs taker)
    - Volume & activity patterns
    - Risk sizing (Monte Carlo Kelly)
    
  Usage:
    cd prediction-market-analysis
    uv run python rookie_analysis.py

  Output: all figures saved to output/rookie/
================================================================================
"""

from pathlib import Path
import json as _json
import duckdb
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Write PNGs into both output/rookie/ (legacy) and static/charts/ (web app)
OUTPUT_DIR = BASE_DIR / "output" / "rookie"
CHARTS_DIR = BASE_DIR / "static" / "charts"
JSON_DIR = BASE_DIR / "static" / "data"
CHART_JSON_DIR = BASE_DIR / "static" / "data" / "charts"
for d in (OUTPUT_DIR, CHARTS_DIR, JSON_DIR, CHART_JSON_DIR):
    d.mkdir(parents=True, exist_ok=True)


def _save_chart_json(filename: str, data: dict):
    """Save chart data as JSON for Plotly rendering."""
    path = CHART_JSON_DIR / filename
    with open(path, "w") as f:
        _json.dump(data, f, separators=(",", ":"))
    print(f"  Saved JSON: {path}")

KALSHI_TRADES = DATA_DIR / "kalshi" / "trades"
KALSHI_MARKETS = DATA_DIR / "kalshi" / "markets"

# Plotting style
plt.rcParams.update({
    "figure.facecolor": "#0e1117",
    "axes.facecolor": "#0e1117",
    "axes.edgecolor": "#333",
    "axes.labelcolor": "#e0e0e0",
    "text.color": "#e0e0e0",
    "xtick.color": "#aaa",
    "ytick.color": "#aaa",
    "grid.color": "#222",
    "grid.alpha": 0.5,
    "font.family": "sans-serif",
    "font.size": 11,
})

COLORS = {
    "primary": "#4fc3f7",
    "secondary": "#81c784",
    "accent": "#ff8a65",
    "danger": "#ef5350",
    "neutral": "#90a4ae",
    "taker": "#ef5350",
    "maker": "#66bb6a",
    "perfect": "#ffd54f",
}


def get_connection():
    """Return a fresh DuckDB connection."""
    return duckdb.connect()


# ══════════════════════════════════════════════════════════════════════════════
#  1. DATASET OVERVIEW — What are we working with?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_1_dataset_overview():
    """Print and visualize basic dataset statistics."""
    print("\n" + "=" * 60)
    print("  1/8  DATASET OVERVIEW")
    print("=" * 60)

    con = get_connection()

    # Trade stats
    trade_stats = con.execute(f"""
        SELECT
            COUNT(*) AS num_trades,
            SUM(count) AS total_contracts,
            COUNT(DISTINCT ticker) AS num_tickers,
            MIN(created_time) AS first_trade,
            MAX(created_time) AS last_trade
        FROM '{KALSHI_TRADES}/*.parquet'
    """).fetchone()

    # Market stats
    market_stats = con.execute(f"""
        SELECT
            COUNT(*) AS num_markets,
            COUNT(DISTINCT event_ticker) AS num_events,
            SUM(CASE WHEN status = 'finalized' THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN result = 'yes' THEN 1 ELSE 0 END) AS resolved_yes,
            SUM(CASE WHEN result = 'no' THEN 1 ELSE 0 END) AS resolved_no
        FROM '{KALSHI_MARKETS}/*.parquet'
    """).fetchone()

    print(f"\n  Kalshi Trades:     {trade_stats[0]:>15,}")
    print(f"  Total Contracts:   {trade_stats[1]:>15,}")
    print(f"  Unique Markets:    {trade_stats[2]:>15,}")
    print(f"  Date Range:        {str(trade_stats[3])[:10]} → {str(trade_stats[4])[:10]}")
    print(f"\n  Markets Listed:    {market_stats[0]:>15,}")
    print(f"  Unique Events:     {market_stats[1]:>15,}")
    print(f"  Resolved:          {market_stats[2]:>15,}")
    print(f"    → Yes:           {market_stats[3]:>15,}")
    print(f"    → No:            {market_stats[4]:>15,}")

    # Volume over time (monthly)
    df = con.execute(f"""
        SELECT
            DATE_TRUNC('month', created_time) AS month,
            COUNT(*) AS num_trades,
            SUM(count) AS contracts
        FROM '{KALSHI_TRADES}/*.parquet'
        GROUP BY month
        ORDER BY month
    """).df()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1.bar(df["month"], df["num_trades"] / 1e6, width=25, color=COLORS["primary"], alpha=0.85)
    ax1.set_ylabel("Trades (millions)")
    ax1.set_title("Monthly Trading Activity on Kalshi", fontsize=16, fontweight="bold", pad=15)
    ax1.grid(True, axis="y")

    ax2.bar(df["month"], df["contracts"] / 1e6, width=25, color=COLORS["secondary"], alpha=0.85)
    ax2.set_ylabel("Contracts (millions)")
    ax2.set_xlabel("Date")
    ax2.grid(True, axis="y")

    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "1_dataset_overview.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Saved: {OUTPUT_DIR / '1_dataset_overview.png'}")

    # Export chart JSON for Plotly
    _save_chart_json("1_dataset_overview.json", {
        "months": [str(m)[:10] for m in df["month"]],
        "trades_millions": (df["num_trades"] / 1e6).round(3).tolist(),
        "contracts_millions": (df["contracts"] / 1e6).round(3).tolist(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  2. CALIBRATION CURVE — Are prediction markets accurate?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_2_calibration_curve():
    """
    The most fundamental chart in prediction markets.
    If a contract trades at 70 cents, does the event happen ~70% of the time?
    Perfect calibration = all points on the diagonal.
    """
    print("\n" + "=" * 60)
    print("  2/8  CALIBRATION CURVE")
    print("=" * 60)

    con = get_connection()
    df = con.execute(f"""
        WITH resolved_markets AS (
            SELECT ticker, result
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE status = 'finalized' AND result IN ('yes', 'no')
        ),
        all_positions AS (
            -- Taker side
            SELECT
                CASE WHEN t.taker_side = 'yes' THEN t.yes_price ELSE t.no_price END AS price,
                CASE WHEN t.taker_side = m.result THEN 1 ELSE 0 END AS won
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
            UNION ALL
            -- Maker side (counterparty)
            SELECT
                CASE WHEN t.taker_side = 'yes' THEN t.no_price ELSE t.yes_price END AS price,
                CASE WHEN t.taker_side != m.result THEN 1 ELSE 0 END AS won
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
        )
        SELECT
            price,
            COUNT(*) AS total_trades,
            SUM(won) AS wins,
            100.0 * SUM(won) / COUNT(*) AS win_rate
        FROM all_positions
        WHERE price BETWEEN 1 AND 99
        GROUP BY price
        ORDER BY price
    """).df()

    fig, ax = plt.subplots(figsize=(10, 10))

    # Scatter: size proportional to trade count
    sizes = np.clip(df["total_trades"] / df["total_trades"].max() * 200, 20, 200)
    scatter = ax.scatter(
        df["price"], df["win_rate"],
        s=sizes, alpha=0.8, c=COLORS["primary"], edgecolors="white", linewidths=0.3,
        zorder=3
    )

    # Perfect calibration line
    ax.plot([0, 100], [0, 100], "--", color=COLORS["perfect"], linewidth=2,
            label="Perfect Calibration", zorder=2)

    # Highlight longshot zone
    ax.axvspan(0, 15, alpha=0.08, color=COLORS["danger"], label="Longshot Zone (overpriced)")

    ax.set_xlabel("Contract Price (cents = implied probability %)", fontsize=13)
    ax.set_ylabel("Actual Win Rate (%)", fontsize=13)
    ax.set_title("Market Calibration: Do Prices Match Reality?", fontsize=16, fontweight="bold", pad=15)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=11)
    ax.grid(True, alpha=0.3)

    # Annotation
    ax.annotate(
        "Points above the line = prices\nwere too LOW (underpriced)\n\n"
        "Points below = prices were\ntoo HIGH (overpriced)",
        xy=(75, 30), fontsize=10, color="#aaa",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#1a1a2e", edgecolor="#333"),
    )

    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "2_calibration_curve.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / '2_calibration_curve.png'}")

    # Export chart JSON for Plotly
    _save_chart_json("2_calibration_curve.json", {
        "price": df["price"].tolist(),
        "win_rate": df["win_rate"].round(3).tolist(),
        "total_trades": df["total_trades"].tolist(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  3. LONGSHOT BIAS — Cheap contracts are systematically overpriced
# ══════════════════════════════════════════════════════════════════════════════
def analysis_3_longshot_bias():
    """
    One of the most famous findings in prediction markets:
    contracts priced at 1-5 cents win far LESS than their price implies.
    
    This is "longshot bias" — people overpay for unlikely outcomes,
    similar to how lottery tickets are overpriced.
    """
    print("\n" + "=" * 60)
    print("  3/8  LONGSHOT BIAS")
    print("=" * 60)

    con = get_connection()
    df = con.execute(f"""
        WITH resolved_markets AS (
            SELECT ticker, result
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE status = 'finalized' AND result IN ('yes', 'no')
        ),
        trades_with_results AS (
            SELECT
                t.yes_price,
                t.count,
                t.taker_side,
                m.result,
                CASE WHEN t.taker_side = m.result THEN 1 ELSE 0 END AS taker_won
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
        )
        SELECT
            yes_price AS price,
            COUNT(*) AS num_trades,
            SUM(count) AS total_contracts,
            AVG(CASE WHEN taker_side = 'yes' THEN taker_won ELSE NULL END) AS yes_taker_win_rate,
            AVG(CASE WHEN taker_side = 'no' THEN taker_won ELSE NULL END) AS no_taker_win_rate
        FROM trades_with_results
        WHERE yes_price BETWEEN 1 AND 20
        GROUP BY yes_price
        ORDER BY yes_price
    """).df()

    # For each price level, compute the expected return per dollar
    # If you buy YES at price p, you pay p cents and win 100 cents with probability = actual_win_rate
    # Expected value per dollar = (win_rate * 100) / price
    df["implied_prob"] = df["price"] / 100.0
    if df["yes_taker_win_rate"].notna().any():
        df["actual_win_rate"] = df["yes_taker_win_rate"].fillna(df["implied_prob"])
    else:
        df["actual_win_rate"] = df["implied_prob"]
    df["ev_per_dollar"] = df["actual_win_rate"] * 100 / df["price"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Left: implied vs actual probability
    x = np.arange(len(df))
    width = 0.35
    ax1.bar(x - width / 2, df["implied_prob"] * 100, width, label="Implied Probability (Price)",
            color=COLORS["primary"], alpha=0.85)
    ax1.bar(x + width / 2, df["actual_win_rate"] * 100, width, label="Actual Win Rate",
            color=COLORS["accent"], alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{p}¢' for p in df["price"]])
    ax1.set_xlabel("Contract Price", fontsize=12)
    ax1.set_ylabel("Probability (%)", fontsize=12)
    ax1.set_title("Implied vs Actual Probability", fontsize=14, fontweight="bold")
    ax1.legend(fontsize=10)
    ax1.grid(True, axis="y", alpha=0.3)

    # Right: expected value per dollar (1.0 = fair)
    colors = [COLORS["danger"] if ev < 1.0 else COLORS["secondary"] for ev in df["ev_per_dollar"]]
    ax2.bar(x, df["ev_per_dollar"], color=colors, alpha=0.85)
    ax2.axhline(y=1.0, color=COLORS["perfect"], linestyle="--", linewidth=2, label="Fair value ($1.00)")
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'{p}¢' for p in df["price"]])
    ax2.set_xlabel("Contract Price", fontsize=12)
    ax2.set_ylabel("Expected Return per $1", fontsize=12)
    ax2.set_title("💸 Return per Dollar (< $1 = losing bet)", fontsize=14, fontweight="bold")
    ax2.legend(fontsize=10)
    ax2.grid(True, axis="y", alpha=0.3)

    fig.suptitle("🎰 Longshot Bias: Cheap Contracts Are Overpriced", fontsize=18, fontweight="bold", y=1.02)
    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "3_longshot_bias.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / '3_longshot_bias.png'}")

    # Export chart JSON for Plotly
    _save_chart_json("3_longshot_bias.json", {
        "price": df["price"].tolist(),
        "implied_prob": (df["implied_prob"] * 100).round(3).tolist(),
        "actual_win_rate": (df["actual_win_rate"] * 100).round(3).tolist(),
        "ev_per_dollar": df["ev_per_dollar"].round(4).tolist(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  4. MAKER vs TAKER RETURNS — Who's making money?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_4_maker_vs_taker():
    """
    Every trade has a maker (passive limit order) and taker (aggressive market order).
    This shows the systematic wealth transfer from takers to makers.
    
    Key insight: Makers earn a small structural edge at almost every price level.
    Takers pay it. This is WHY market-making is profitable.
    """
    print("\n" + "=" * 60)
    print("  4/8  MAKER vs TAKER RETURNS")
    print("=" * 60)

    con = get_connection()
    df = con.execute(f"""
        WITH resolved_markets AS (
            SELECT ticker, result
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE status = 'finalized' AND result IN ('yes', 'no')
        ),
        taker_positions AS (
            SELECT
                CASE WHEN t.taker_side = 'yes' THEN t.yes_price ELSE t.no_price END AS price,
                CASE WHEN t.taker_side = m.result THEN 1.0 ELSE 0.0 END AS won,
                t.count AS contracts
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
        ),
        maker_positions AS (
            SELECT
                CASE WHEN t.taker_side = 'yes' THEN t.no_price ELSE t.yes_price END AS price,
                CASE WHEN t.taker_side != m.result THEN 1.0 ELSE 0.0 END AS won,
                t.count AS contracts
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
        ),
        taker_stats AS (
            SELECT price,
                   AVG(won) - price / 100.0 AS excess_return,
                   SUM(contracts * (won - price / 100.0)) AS pnl,
                   COUNT(*) AS n_trades
            FROM taker_positions GROUP BY price
        ),
        maker_stats AS (
            SELECT price,
                   AVG(won) - price / 100.0 AS excess_return,
                   SUM(contracts * (won - price / 100.0)) AS pnl,
                   COUNT(*) AS n_trades
            FROM maker_positions GROUP BY price
        )
        SELECT
            t.price,
            t.excess_return AS taker_excess,
            t.pnl AS taker_pnl,
            t.n_trades AS taker_n,
            m.excess_return AS maker_excess,
            m.pnl AS maker_pnl,
            m.n_trades AS maker_n
        FROM taker_stats t
        JOIN maker_stats m ON t.price = m.price
        WHERE t.price BETWEEN 1 AND 99
        ORDER BY t.price
    """).df()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Top: Excess returns by price
    ax1.fill_between(df["price"], df["taker_excess"] * 100, 0,
                     where=df["taker_excess"] * 100 < 0, alpha=0.3, color=COLORS["taker"])
    ax1.fill_between(df["price"], df["taker_excess"] * 100, 0,
                     where=df["taker_excess"] * 100 >= 0, alpha=0.3, color=COLORS["secondary"])
    ax1.plot(df["price"], df["taker_excess"] * 100, color=COLORS["taker"],
             linewidth=2, label="Taker Excess Return")
    ax1.plot(df["price"], df["maker_excess"] * 100, color=COLORS["maker"],
             linewidth=2, label="Maker Excess Return")
    ax1.axhline(y=0, color="white", linestyle="-", linewidth=0.5, alpha=0.5)
    ax1.set_xlabel("Contract Price (cents)")
    ax1.set_ylabel("Excess Return (percentage points)")
    ax1.set_title("📈 Excess Return by Price Level", fontsize=14, fontweight="bold")
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(1, 99)

    # Bottom: Cumulative P&L
    ax2.bar(df["price"], df["taker_pnl"], color=COLORS["taker"], alpha=0.7, label="Taker P&L", width=1)
    ax2.bar(df["price"], df["maker_pnl"], color=COLORS["maker"], alpha=0.7, label="Maker P&L", width=1)
    ax2.axhline(y=0, color="white", linestyle="-", linewidth=0.5, alpha=0.5)
    ax2.set_xlabel("Contract Price (cents)")
    ax2.set_ylabel("Profit/Loss (contracts)")
    ax2.set_title("💰 P&L by Price Level (Makers win, Takers lose)", fontsize=14, fontweight="bold")
    ax2.legend(fontsize=11)
    ax2.grid(True, axis="y", alpha=0.3)
    ax2.set_xlim(1, 99)

    total_taker_pnl = df["taker_pnl"].sum()
    total_maker_pnl = df["maker_pnl"].sum()
    print(f"\n  Total Taker P&L: {total_taker_pnl:>+15,.0f} contracts")
    print(f"  Total Maker P&L: {total_maker_pnl:>+15,.0f} contracts")

    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "4_maker_vs_taker.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / '4_maker_vs_taker.png'}")

    # Export chart JSON for Plotly
    _save_chart_json("4_maker_vs_taker.json", {
        "price": df["price"].tolist(),
        "taker_excess": (df["taker_excess"] * 100).round(4).tolist(),
        "maker_excess": (df["maker_excess"] * 100).round(4).tolist(),
        "taker_pnl": df["taker_pnl"].round(0).tolist(),
        "maker_pnl": df["maker_pnl"].round(0).tolist(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  5. TRADE SIZE DISTRIBUTION — Who trades big vs small?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_5_trade_size_distribution():
    """
    Explore how trade sizes are distributed.
    Most trades are small (retail), but a few are massive (institutional?).
    """
    print("\n" + "=" * 60)
    print("  5/8  TRADE SIZE DISTRIBUTION")
    print("=" * 60)

    con = get_connection()
    df = con.execute(f"""
        SELECT
            count AS trade_size,
            taker_side
        FROM '{KALSHI_TRADES}/*.parquet'
        WHERE count >= 1
    """).df()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Left: histogram of trade sizes (log scale)
    bins = np.logspace(0, np.log10(df["trade_size"].max()), 50)
    ax1.hist(df["trade_size"], bins=bins, color=COLORS["primary"], alpha=0.8, edgecolor="none")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Trade Size (contracts)", fontsize=12)
    ax1.set_ylabel("Frequency", fontsize=12)
    ax1.set_title("Trade Size Distribution (log-log)", fontsize=14, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    # Add key stats
    median_size = df["trade_size"].median()
    mean_size = df["trade_size"].mean()
    p99_size = df["trade_size"].quantile(0.99)
    ax1.axvline(median_size, color=COLORS["perfect"], linestyle="--", label=f"Median: {median_size:.0f}")
    ax1.axvline(mean_size, color=COLORS["accent"], linestyle="--", label=f"Mean: {mean_size:.1f}")
    ax1.axvline(p99_size, color=COLORS["danger"], linestyle="--", label=f"99th pctl: {p99_size:.0f}")
    ax1.legend(fontsize=10)

    # Right: cumulative share of volume
    sorted_sizes = np.sort(df["trade_size"].values)
    cumulative_volume = np.cumsum(sorted_sizes) / sorted_sizes.sum()
    percentiles = np.arange(1, len(sorted_sizes) + 1) / len(sorted_sizes)

    ax2.plot(percentiles * 100, cumulative_volume * 100, color=COLORS["secondary"], linewidth=2)
    ax2.set_xlabel("% of Trades (smallest to largest)", fontsize=12)
    ax2.set_ylabel("% of Total Volume", fontsize=12)
    ax2.set_title("Volume Concentration (Lorenz Curve)", fontsize=14, fontweight="bold")
    ax2.plot([0, 100], [0, 100], "--", color=COLORS["neutral"], alpha=0.5, label="Equal distribution")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    # Find what % of trades account for 50% of volume
    idx_50 = np.searchsorted(cumulative_volume, 0.5)
    pct_at_50 = (1 - percentiles[idx_50]) * 100
    ax2.annotate(f"Top {pct_at_50:.1f}% of trades\n= 50% of volume",
                 xy=(percentiles[idx_50] * 100, 50), fontsize=10, color=COLORS["accent"],
                 arrowprops=dict(arrowstyle="->", color=COLORS["accent"]),
                 xytext=(30, 70))

    print(f"\n  Median trade size:  {median_size:.0f} contracts")
    print(f"  Mean trade size:    {mean_size:.1f} contracts")
    print(f"  99th percentile:    {p99_size:.0f} contracts")
    print(f"  Top {pct_at_50:.1f}% of trades = 50% of all volume")

    fig.suptitle("📦 Trade Size Distribution", fontsize=18, fontweight="bold", y=1.02)
    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "5_trade_size_distribution.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / '5_trade_size_distribution.png'}")

    # Export chart JSON for Plotly
    # Bin edges for histogram (don't send 72M raw values)
    hist_counts, hist_edges = np.histogram(df["trade_size"], bins=np.logspace(0, np.log10(df["trade_size"].max()), 50))
    # Downsample lorenz curve to ~500 points
    step = max(1, len(sorted_sizes) // 500)
    _save_chart_json("5_trade_size_distribution.json", {
        "hist_bin_edges": hist_edges.round(2).tolist(),
        "hist_counts": hist_counts.tolist(),
        "lorenz_pct_trades": (percentiles[::step] * 100).round(2).tolist(),
        "lorenz_pct_volume": (cumulative_volume[::step] * 100).round(2).tolist(),
        "median": float(median_size),
        "mean": round(float(mean_size), 1),
        "p99": float(p99_size),
        "top_pct_half_volume": round(float(pct_at_50), 1),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  6. RETURNS BY HOUR — When do informed traders trade?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_6_returns_by_hour():
    """
    Does it matter WHEN you trade?
    Informed traders tend to cluster at certain hours.
    Excess returns vary by time of day.
    """
    print("\n" + "=" * 60)
    print("  6/8  RETURNS BY HOUR OF DAY")
    print("=" * 60)

    con = get_connection()
    df = con.execute(f"""
        WITH resolved_markets AS (
            SELECT ticker, result
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE status = 'finalized' AND result IN ('yes', 'no')
        ),
        trade_data AS (
            SELECT
                EXTRACT(HOUR FROM t.created_time) AS hour,
                CASE WHEN t.taker_side = 'yes' THEN t.yes_price ELSE t.no_price END AS price,
                CASE WHEN t.taker_side = m.result THEN 1.0 ELSE 0.0 END AS won,
                t.count AS contracts
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
        )
        SELECT
            hour,
            AVG(won - price / 100.0) AS excess_return,
            SUM(contracts) AS total_contracts,
            COUNT(*) AS n_trades
        FROM trade_data
        GROUP BY hour
        ORDER BY hour
    """).df()

    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax2 = ax1.twinx()

    # Volume bars (background)
    ax2.bar(df["hour"], df["total_contracts"] / 1e6, color=COLORS["neutral"],
            alpha=0.2, width=0.8, label="Volume (M contracts)")
    ax2.set_ylabel("Volume (millions of contracts)", color="#666")
    ax2.tick_params(axis="y", labelcolor="#666")

    # Excess return line
    colors_bar = [COLORS["danger"] if x < 0 else COLORS["secondary"] for x in df["excess_return"]]
    ax1.bar(df["hour"], df["excess_return"] * 100, color=colors_bar, alpha=0.85, width=0.6)
    ax1.axhline(y=0, color="white", linestyle="-", linewidth=0.5, alpha=0.5)
    ax1.set_xlabel("Hour of Day (UTC)", fontsize=12)
    ax1.set_ylabel("Taker Excess Return (pp)", fontsize=12)
    ax1.set_title("⏰ Excess Return & Volume by Hour of Day",
                   fontsize=16, fontweight="bold", pad=15)
    ax1.set_xlim(-0.5, 23.5)
    ax1.set_xticks(range(0, 24))
    ax1.set_xticklabels([f"{h:02d}" for h in range(24)], fontsize=9)
    ax1.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "6_returns_by_hour.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / '6_returns_by_hour.png'}")

    # Export chart JSON for Plotly
    _save_chart_json("6_returns_by_hour.json", {
        "hour": df["hour"].tolist(),
        "excess_return": (df["excess_return"] * 100).round(4).tolist(),
        "total_contracts_millions": (df["total_contracts"] / 1e6).round(3).tolist(),
        "n_trades": df["n_trades"].tolist(),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  7. CALIBRATION SURFACE (Price × Time) — Where exactly are markets wrong?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_7_calibration_surface():
    """
    Instead of a single calibration curve, build a 2D heatmap of
    mispricing across both price level AND time-to-close.
    
    This is what hedge funds use: bias varies by price AND timing.
    """
    print("\n" + "=" * 60)
    print("  7/8  CALIBRATION SURFACE (Price × Time)")
    print("=" * 60)

    con = get_connection()
    df = con.execute(f"""
        WITH resolved_markets AS (
            SELECT ticker, result, close_time
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE status = 'finalized'
              AND result IN ('yes', 'no')
              AND close_time IS NOT NULL
        ),
        trades_with_time AS (
            SELECT
                CASE WHEN t.taker_side = 'yes' THEN t.yes_price ELSE t.no_price END AS price,
                CASE WHEN t.taker_side = m.result THEN 1.0 ELSE 0.0 END AS won,
                EXTRACT(EPOCH FROM (m.close_time - t.created_time)) / 3600.0 AS hours_to_close
            FROM '{KALSHI_TRADES}/*.parquet' t
            INNER JOIN resolved_markets m ON t.ticker = m.ticker
        ),
        binned AS (
            SELECT
                -- Price bins of 10
                FLOOR(price / 10) * 10 AS price_bin,
                -- Time bins
                CASE
                    WHEN hours_to_close < 1 THEN '< 1h'
                    WHEN hours_to_close < 6 THEN '1-6h'
                    WHEN hours_to_close < 24 THEN '6-24h'
                    WHEN hours_to_close < 72 THEN '1-3d'
                    WHEN hours_to_close < 168 THEN '3-7d'
                    WHEN hours_to_close < 720 THEN '7-30d'
                    ELSE '> 30d'
                END AS time_bin,
                CASE
                    WHEN hours_to_close < 1 THEN 0
                    WHEN hours_to_close < 6 THEN 1
                    WHEN hours_to_close < 24 THEN 2
                    WHEN hours_to_close < 72 THEN 3
                    WHEN hours_to_close < 168 THEN 4
                    WHEN hours_to_close < 720 THEN 5
                    ELSE 6
                END AS time_order,
                won,
                price
            FROM trades_with_time
            WHERE price BETWEEN 1 AND 99
              AND hours_to_close > 0
        )
        SELECT
            price_bin,
            time_bin,
            time_order,
            COUNT(*) AS n_trades,
            AVG(won) * 100 AS actual_win_rate,
            AVG(price) AS avg_price,
            AVG(won) * 100 - AVG(price) AS mispricing
        FROM binned
        GROUP BY price_bin, time_bin, time_order
        HAVING COUNT(*) >= 100
        ORDER BY price_bin, time_order
    """).df()

    # Pivot for heatmap
    pivot = df.pivot_table(index="price_bin", columns="time_order", values="mispricing")
    time_labels = ["< 1h", "1-6h", "6-24h", "1-3d", "3-7d", "7-30d", "> 30d"]

    fig, ax = plt.subplots(figsize=(12, 8))

    vmax = max(abs(pivot.values.min()), abs(pivot.values.max()))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", norm=norm, origin="lower")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([time_labels[int(c)] for c in pivot.columns], fontsize=11)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([f"{int(p)}-{int(p) + 10}¢" for p in pivot.index], fontsize=11)

    # Add text annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                color = "black" if abs(val) < vmax * 0.5 else "white"
                ax.text(j, i, f"{val:+.1f}", ha="center", va="center", fontsize=9,
                        fontweight="bold", color=color)

    cbar = plt.colorbar(im, ax=ax, label="Mispricing (pp): Actual Win Rate - Implied Prob")
    ax.set_xlabel("Time to Market Close", fontsize=13)
    ax.set_ylabel("Price Bucket", fontsize=13)
    ax.set_title("🗺️ Calibration Surface: Where & When Markets Are Wrong",
                 fontsize=16, fontweight="bold", pad=15)

    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "7_calibration_surface.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / '7_calibration_surface.png'}")

    # Export chart JSON for Plotly
    time_labels_map = {0: "< 1h", 1: "1-6h", 2: "6-24h", 3: "1-3d", 4: "3-7d", 5: "7-30d", 6: "> 30d"}
    _save_chart_json("7_calibration_surface.json", {
        "price_bins": [f"{int(p)}-{int(p)+10}¢" for p in pivot.index],
        "time_bins": [time_labels_map[int(c)] for c in pivot.columns],
        "mispricing": [[round(v, 2) if not np.isnan(v) else None for v in row] for row in pivot.values.tolist()],
    })


# ══════════════════════════════════════════════════════════════════════════════
#  8. MONTE CARLO KELLY — Risk sizing under uncertainty
# ══════════════════════════════════════════════════════════════════════════════
def analysis_8_monte_carlo_kelly():
    """
    Standard Kelly criterion over-sizes because it treats estimated edge as certain.
    
    Monte Carlo resampling shows the DISTRIBUTION of possible drawdowns,
    letting you size to survive the 95th percentile worst case, not just the average.
    """
    print("\n" + "=" * 60)
    print("  8/8  MONTE CARLO KELLY SIZING")
    print("=" * 60)

    con = get_connection()
    
    # Get returns for a specific signal: longshot YES takers in resolved markets (5-15 cent range)
    df = con.execute(f"""
        WITH resolved_markets AS (
            SELECT ticker, result
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE status = 'finalized' AND result IN ('yes', 'no')
        )
        SELECT
            t.yes_price AS price,
            CASE WHEN t.taker_side = m.result THEN 1.0 ELSE 0.0 END AS won,
            t.count AS contracts
        FROM '{KALSHI_TRADES}/*.parquet' t
        INNER JOIN resolved_markets m ON t.ticker = m.ticker
        WHERE t.taker_side = 'yes'
          AND t.yes_price BETWEEN 5 AND 15
    """).df()

    if len(df) < 100:
        print("  ⚠️  Not enough trades in 5-15 cent range for Monte Carlo. Skipping.")
        return

    # Calculate per-trade returns: won * (100 - price) / price  if won, else -1
    df["return_pct"] = np.where(df["won"] == 1, (100 - df["price"]) / df["price"], -1.0)
    returns = df["return_pct"].values

    avg_return = returns.mean()
    win_rate = df["won"].mean()
    implied_prob = df["price"].mean() / 100

    print(f"\n  Signal: Buy YES at 5-15 cents on resolved markets")
    print(f"  Number of trades:  {len(returns):,}")
    print(f"  Average return:    {avg_return:+.4f} ({avg_return * 100:+.2f}%)")
    print(f"  Win rate:          {win_rate:.4f} ({win_rate * 100:.2f}%)")
    print(f"  Implied prob:      {implied_prob:.4f} ({implied_prob * 100:.2f}%)")
    print(f"  Edge:              {(win_rate - implied_prob) * 100:+.2f} pp")

    # Monte Carlo simulation
    n_simulations = 5000
    n_trades_per_sim = min(200, len(returns))
    
    max_drawdowns = []
    final_returns = []
    
    rng = np.random.default_rng(42)
    for _ in range(n_simulations):
        # Bootstrap: resample returns with replacement
        sampled = rng.choice(returns, size=n_trades_per_sim, replace=True)
        # Simulate equity curve with Kelly fraction
        equity = np.cumprod(1 + sampled * 0.05)  # 5% Kelly fraction
        running_max = np.maximum.accumulate(equity)
        drawdown = (running_max - equity) / running_max
        max_drawdowns.append(drawdown.max())
        final_returns.append(equity[-1] - 1)

    max_drawdowns = np.array(max_drawdowns)
    final_returns = np.array(final_returns)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Top-left: Drawdown distribution
    ax = axes[0, 0]
    ax.hist(max_drawdowns * 100, bins=50, color=COLORS["danger"], alpha=0.8, edgecolor="none")
    p95 = np.percentile(max_drawdowns, 95) * 100
    p50 = np.percentile(max_drawdowns, 50) * 100
    ax.axvline(p50, color=COLORS["perfect"], linestyle="--", linewidth=2,
               label=f"Median: {p50:.1f}%")
    ax.axvline(p95, color="white", linestyle="--", linewidth=2,
               label=f"95th pctl: {p95:.1f}%")
    ax.set_xlabel("Max Drawdown (%)")
    ax.set_ylabel("Frequency")
    ax.set_title("Drawdown Distribution (5% Kelly)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)

    # Top-right: Final return distribution
    ax = axes[0, 1]
    positive = final_returns[final_returns >= 0]
    negative = final_returns[final_returns < 0]
    ax.hist(positive * 100, bins=40, color=COLORS["secondary"], alpha=0.8,
            edgecolor="none", label=f"Profitable ({len(positive) / len(final_returns) * 100:.0f}%)")
    ax.hist(negative * 100, bins=40, color=COLORS["danger"], alpha=0.8,
            edgecolor="none", label=f"Losing ({len(negative) / len(final_returns) * 100:.0f}%)")
    ax.axvline(0, color="white", linestyle="-", linewidth=1)
    ax.set_xlabel("Total Return (%)")
    ax.set_ylabel("Frequency")
    ax.set_title("Return Distribution (5% Kelly)", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)

    # Bottom-left: Sample equity curves
    ax = axes[1, 0]
    rng2 = np.random.default_rng(42)
    for i in range(50):
        sampled = rng2.choice(returns, size=n_trades_per_sim, replace=True)
        equity = np.cumprod(1 + sampled * 0.05)
        color = COLORS["secondary"] if equity[-1] > 1 else COLORS["danger"]
        ax.plot(equity, alpha=0.15, color=color, linewidth=0.8)
    ax.axhline(1.0, color="white", linestyle="--", linewidth=0.5)
    ax.set_xlabel("Trade #")
    ax.set_ylabel("Portfolio Value (starting $1)")
    ax.set_title("50 Sample Equity Curves", fontsize=13, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Bottom-right: Kelly fraction sensitivity
    ax = axes[1, 1]
    kelly_fractions = np.linspace(0.01, 0.30, 30)
    median_returns = []
    p5_returns = []
    p95_returns_list = []
    
    rng3 = np.random.default_rng(42)
    for kf in kelly_fractions:
        sim_finals = []
        for _ in range(1000):
            sampled = rng3.choice(returns, size=n_trades_per_sim, replace=True)
            equity = np.cumprod(1 + sampled * kf)
            sim_finals.append(equity[-1] - 1)
        sim_finals = np.array(sim_finals)
        median_returns.append(np.median(sim_finals))
        p5_returns.append(np.percentile(sim_finals, 5))
        p95_returns_list.append(np.percentile(sim_finals, 95))

    ax.plot(kelly_fractions * 100, np.array(median_returns) * 100,
            color=COLORS["primary"], linewidth=2, label="Median return")
    ax.fill_between(kelly_fractions * 100,
                     np.array(p5_returns) * 100, np.array(p95_returns_list) * 100,
                     alpha=0.2, color=COLORS["primary"], label="5th-95th percentile")
    ax.axhline(0, color="white", linestyle="--", linewidth=0.5)
    ax.set_xlabel("Kelly Fraction (%)")
    ax.set_ylabel("Total Return (%)")
    ax.set_title("Kelly Fraction Sensitivity", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.suptitle("Monte Carlo Risk Sizing (Longshot Signal: 5-15¢ YES)",
                 fontsize=18, fontweight="bold", y=1.01)
    plt.tight_layout()
    for dest in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(dest / "8_monte_carlo_kelly.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Saved: {OUTPUT_DIR / '8_monte_carlo_kelly.png'}")

    # Export chart JSON for Plotly
    # Re-run 50 equity curves for JSON export
    equity_curves = []
    rng4 = np.random.default_rng(42)
    for i in range(50):
        sampled = rng4.choice(returns, size=n_trades_per_sim, replace=True)
        equity = np.cumprod(1 + sampled * 0.05)
        equity_curves.append(equity.round(4).tolist())

    _save_chart_json("8_monte_carlo_kelly.json", {
        "drawdowns": (max_drawdowns * 100).round(2).tolist(),
        "final_returns": (final_returns * 100).round(2).tolist(),
        "equity_curves": equity_curves,
        "kelly_fractions": (kelly_fractions * 100).round(2).tolist(),
        "kelly_median_return": (np.array(median_returns) * 100).round(2).tolist(),
        "kelly_p5_return": (np.array(p5_returns) * 100).round(2).tolist(),
        "kelly_p95_return": (np.array(p95_returns_list) * 100).round(2).tolist(),
        "stats": {
            "avg_return_pct": round(avg_return * 100, 2),
            "win_rate_pct": round(win_rate * 100, 2),
            "implied_prob_pct": round(implied_prob * 100, 2),
            "n_trades": len(returns),
        },
    })


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     PREDICTION MARKET ROOKIE ANALYSIS                      ║
    ║     ─────────────────────────────────────────               ║
    ║     8 visualizations to understand prediction markets       ║
    ║     from 400M+ real trades (Kalshi dataset)                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Check data exists
    if not KALSHI_TRADES.exists():
        print(f"  ERROR: Data not found at {KALSHI_TRADES}")
        print(f"     Run 'make setup' first to download the dataset.")
        return

    analyses = [
        ("Dataset Overview",        analysis_1_dataset_overview),
        ("Calibration Curve",       analysis_2_calibration_curve),
        ("Longshot Bias",           analysis_3_longshot_bias),
        ("Maker vs Taker Returns",  analysis_4_maker_vs_taker),
        ("Trade Size Distribution", analysis_5_trade_size_distribution),
        ("Returns by Hour",         analysis_6_returns_by_hour),
        ("Calibration Surface",     analysis_7_calibration_surface),
        ("Monte Carlo Kelly",       analysis_8_monte_carlo_kelly),
    ]

    for i, (name, func) in enumerate(analyses, 1):
        try:
            func()
        except Exception as e:
            print(f"\n  ERROR: Analysis {i} ({name}) failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("ALL DONE!")
    print(f"  Output saved to: {OUTPUT_DIR}/")
    print("=" * 60)
    print("""
  What each chart teaches you:
  ───────────────────────────
  1. Dataset Overview     → How big is this market? Growth trends
  2. Calibration Curve    → Are market prices = true probabilities?
  3. Longshot Bias        → Cheap bets are overpriced (like lottery tickets)
  4. Maker vs Taker       → Passive liquidity providers win systematically
  5. Trade Size Dist.     → Most trades are tiny, a few are massive
  6. Returns by Hour      → Some hours have better/worse edge
  7. Calibration Surface  → WHERE and WHEN markets are most wrong
  8. Monte Carlo Kelly    → How to size bets using uncertainty, not certainty
    """)


if __name__ == "__main__":
    main()
