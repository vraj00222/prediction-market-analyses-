from analyses.utils import get_connection, _save, _save_json, COLORS, KALSHI_MARKETS
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def spread_liquidity():
    """Analyze bid-ask spreads on Kalshi, their relationship to volume and time-to-expiry."""
    con = get_connection()
    spread_data = con.sql(f"""
        SELECT yes_bid, yes_ask, no_bid, no_ask, volume, open_interest, last_price,
            EXTRACT(EPOCH FROM (close_time - created_time)) / 3600.0 AS hours_to_close, result
        FROM '{KALSHI_MARKETS}/*.parquet'
        WHERE yes_bid > 0 AND yes_ask > 0 AND yes_ask > yes_bid AND close_time > created_time
    """).fetchdf()
    spread_data["spread"] = spread_data["yes_ask"] - spread_data["yes_bid"]
    spread_data["mid"] = (spread_data["yes_ask"] + spread_data["yes_bid"]) / 2
    total_markets = len(spread_data)
    avg_spread = spread_data["spread"].mean()
    median_spread = spread_data["spread"].median()
    spread_hist = np.histogram(spread_data["spread"].clip(0, 50), bins=50)
    hist_counts = spread_hist[0].tolist()
    hist_edges = [round(e, 1) for e in spread_hist[1].tolist()]
    spread_data["vol_bin"] = pd.qcut(spread_data["volume"].clip(lower=1), q=10, duplicates="drop")
    vol_spread = spread_data.groupby("vol_bin", observed=True).agg(
        avg_spread=("spread", "mean"),
        median_spread=("spread", "median"),
        count=("spread", "count"),
        avg_volume=("volume", "mean"),
    ).reset_index()
    spread_data["hours_bin"] = pd.cut(
        spread_data["hours_to_close"].clip(0, 720),
        bins=[0, 1, 6, 24, 72, 168, 336, 720],
        labels=["<1h", "1-6h", "6-24h", "1-3d", "3-7d", "1-2w", "2-4w"]
    )
    time_spread = spread_data.groupby("hours_bin", observed=True).agg(
        avg_spread=("spread", "mean"),
        median_spread=("spread", "median"),
        count=("spread", "count"),
    ).reset_index()
    spread_data["price_bucket"] = (spread_data["mid"] / 5).round() * 5
    price_spread = spread_data.groupby("price_bucket", observed=True).agg(
        avg_spread=("spread", "mean"),
        count=("spread", "count"),
    ).reset_index()
    price_spread = price_spread[(price_spread["price_bucket"] >= 5) & (price_spread["price_bucket"] <= 95)]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax = axes[0, 0]
    ax.bar([(hist_edges[i] + hist_edges[i + 1]) / 2 for i in range(len(hist_counts))], hist_counts, width=1, color=COLORS["primary"], alpha=0.8)
    ax.axvline(avg_spread, color=COLORS["accent"], linestyle="--", label=f"Mean: {avg_spread:.1f}¢")
    ax.axvline(median_spread, color=COLORS["secondary"], linestyle="--", label=f"Median: {median_spread:.0f}¢")
    ax.set_xlabel("Bid-Ask Spread (¢)")
    ax.set_ylabel("Number of Markets")
    ax.set_title("Spread Distribution", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax2 = axes[0, 1]
    ax2.plot(vol_spread["avg_volume"], vol_spread["avg_spread"], "o-", color=COLORS["primary"], markersize=8, linewidth=2)
    ax2.set_xlabel("Average Volume (contracts)")
    ax2.set_ylabel("Average Spread (¢)")
    ax2.set_title("Spread vs Volume", fontsize=12, fontweight="bold")
    ax2.set_xscale("log")
    ax2.grid(alpha=0.3)
    ax3 = axes[1, 0]
    x_pos = range(len(time_spread))
    ax3.bar(x_pos, time_spread["avg_spread"], color=COLORS["accent"], alpha=0.85)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(time_spread["hours_bin"], fontsize=10)
    ax3.set_ylabel("Average Spread (¢)")
    ax3.set_title("Spread vs Time to Close", fontsize=12, fontweight="bold")
    for i, row in time_spread.iterrows():
        ax3.text(list(x_pos)[i], row["avg_spread"] + 0.3, f'{row["count"]:,}', ha="center", fontsize=8, color="#999")
    ax3.grid(axis="y", alpha=0.3)
    ax4 = axes[1, 1]
    ax4.plot(price_spread["price_bucket"], price_spread["avg_spread"], "o-", color=COLORS["secondary"], markersize=6, linewidth=2)
    ax4.set_xlabel("Mid Price (¢)")
    ax4.set_ylabel("Average Spread (¢)")
    ax4.set_title("Spread vs Price (Liquidity Smile)", fontsize=12, fontweight="bold")
    ax4.grid(alpha=0.3)
    fig.tight_layout(pad=2.0)
    _save(fig, "12_spread_liquidity.png")
    _save_json("12_spread_liquidity.json", {
        "hist_edges": hist_edges,
        "hist_counts": hist_counts,
        "avg_spread": round(avg_spread, 2),
        "median_spread": round(median_spread, 1),
        "total_markets": total_markets,
        "vol_x": [round(v, 1) for v in vol_spread["avg_volume"]],
        "vol_y": [round(v, 2) for v in vol_spread["avg_spread"]],
        "time_labels": time_spread["hours_bin"].tolist(),
        "time_spread": [round(v, 2) for v in time_spread["avg_spread"]],
        "time_counts": time_spread["count"].tolist(),
        "price_x": price_spread["price_bucket"].tolist(),
        "price_y": [round(v, 2) for v in price_spread["avg_spread"]],
    })
    return {"avg_spread": avg_spread, "median_spread": median_spread}
