from analyses.utils import get_connection, _save, _save_json, COLORS, KALSHI_TRADES, KALSHI_MARKETS, POLY_TRADES, POLY_MARKETS, POLY_BLOCKS
import numpy as np
import matplotlib.pyplot as plt

def platform_comparison():
    """Compare Kalshi and Polymarket: monthly trades, volume growth, market counts."""
    con = get_connection()
    kalshi_monthly = con.sql(f"""
        SELECT DATE_TRUNC('month', created_time) AS month, COUNT(*) AS trades, SUM(count) AS contracts
        FROM '{KALSHI_TRADES}/*.parquet'
        GROUP BY 1 ORDER BY 1
    """).fetchdf()
    poly_monthly = con.sql(f"""
        SELECT DATE_TRUNC('month', CAST(b.timestamp AS TIMESTAMP)) AS month, COUNT(*) AS trades, SUM(CAST(t.taker_amount AS DOUBLE) / 1e6) AS volume_usdc
        FROM '{POLY_TRADES}/*.parquet' t
        JOIN '{POLY_BLOCKS}/*.parquet' b ON t.block_number = b.block_number
        GROUP BY 1 HAVING month IS NOT NULL ORDER BY 1
    """).fetchdf().dropna(subset=["month"])
    kalshi_markets_count = con.sql(f"SELECT COUNT(DISTINCT ticker) FROM '{KALSHI_MARKETS}/*.parquet'").fetchone()[0]
    poly_markets_count = con.sql(f"SELECT COUNT(*) FROM '{POLY_MARKETS}/*.parquet'").fetchone()[0]
    kalshi_total = int(kalshi_monthly["trades"].sum())
    poly_total = int(poly_monthly["trades"].sum())
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    ax = axes[0]
    ax.bar(kalshi_monthly["month"], kalshi_monthly["trades"] / 1e6, width=20, alpha=0.8, color=COLORS["kalshi"], label="Kalshi")
    ax.bar(poly_monthly["month"], poly_monthly["trades"] / 1e6, width=20, alpha=0.8, color=COLORS["poly"], label="Polymarket")
    ax.set_ylabel("Trades (millions)")
    ax.set_title("Monthly Trade Count: Kalshi vs Polymarket", fontsize=14, fontweight="bold", pad=12)
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    ax2 = axes[1]
    k_cum = kalshi_monthly["trades"].cumsum() / 1e6
    p_cum = poly_monthly["trades"].cumsum() / 1e6
    ax2.plot(kalshi_monthly["month"], k_cum, color=COLORS["kalshi"], linewidth=2.5, label="Kalshi")
    ax2.plot(poly_monthly["month"], p_cum, color=COLORS["poly"], linewidth=2.5, label="Polymarket")
    ax2.fill_between(kalshi_monthly["month"], k_cum, alpha=0.15, color=COLORS["kalshi"])
    ax2.fill_between(poly_monthly["month"], p_cum, alpha=0.15, color=COLORS["poly"])
    ax2.set_ylabel("Cumulative Trades (millions)")
    ax2.set_title("Cumulative Growth", fontsize=14, fontweight="bold", pad=12)
    ax2.legend(fontsize=11)
    ax2.grid(axis="y", alpha=0.3)
    fig.tight_layout(pad=2.0)
    _save(fig, "9_platform_comparison.png")
    _save_json("9_platform_comparison.json", {
        "kalshi_months": [str(d.date()) for d in kalshi_monthly["month"]],
        "kalshi_trades_m": [round(v / 1e6, 2) for v in kalshi_monthly["trades"]],
        "kalshi_cum_m": [round(v, 2) for v in k_cum],
        "poly_months": [str(d.date()) for d in poly_monthly["month"]],
        "poly_trades_m": [round(v / 1e6, 2) for v in poly_monthly["trades"]],
        "poly_cum_m": [round(v, 2) for v in p_cum],
        "kalshi_total": kalshi_total,
        "poly_total": poly_total,
        "kalshi_markets": kalshi_markets_count,
        "poly_markets": poly_markets_count,
    })
    return {
        "kalshi_total": kalshi_total,
        "poly_total": poly_total,
        "kalshi_markets": kalshi_markets_count,
        "poly_markets": poly_markets_count,
    }
