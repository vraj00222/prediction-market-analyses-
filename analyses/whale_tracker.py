from analyses.utils import get_connection, _save, _save_json, COLORS, POLY_TRADES, POLY_BLOCKS
import numpy as np
import matplotlib.pyplot as plt

def whale_tracker():
    """Analyze trading concentration by Polymarket address."""
    con = get_connection()
    trader_stats = con.sql(f"""
        SELECT taker AS address, COUNT(*) AS trade_count, SUM(CAST(taker_amount AS DOUBLE) / 1e6) AS volume_usdc
        FROM '{POLY_TRADES}/*.parquet'
        GROUP BY 1 ORDER BY volume_usdc DESC
    """).fetchdf()
    total_traders = len(trader_stats)
    total_trades = int(trader_stats["trade_count"].sum())
    total_volume = float(trader_stats["volume_usdc"].sum())
    top20 = trader_stats.head(20).copy()
    top20["pct_volume"] = top20["volume_usdc"] / total_volume * 100
    top1_pct = trader_stats.head(max(1, total_traders // 100))["volume_usdc"].sum() / total_volume * 100
    top10_pct = trader_stats.head(max(1, total_traders // 10))["volume_usdc"].sum() / total_volume * 100
    top100_volume = trader_stats.head(100)["volume_usdc"].sum() / total_volume * 100
    sorted_vol = np.sort(trader_stats["volume_usdc"].values)
    cum_vol = np.cumsum(sorted_vol)
    cum_vol_pct = cum_vol / cum_vol[-1] * 100
    trader_pct = np.arange(1, len(sorted_vol) + 1) / len(sorted_vol) * 100
    n = len(trader_pct)
    step = max(1, n // 200)
    idx = list(range(0, n, step))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    lorenz_x = [round(trader_pct[i], 2) for i in idx]
    lorenz_y = [round(cum_vol_pct[i], 2) for i in idx]
    n_g = len(sorted_vol)
    gini = (2 * np.sum(np.arange(1, n_g + 1) * sorted_vol) - (n_g + 1) * np.sum(sorted_vol)) / (n_g * np.sum(sorted_vol))
    trade_counts = trader_stats["trade_count"].values
    bins_labels = ["1", "2-10", "11-100", "101-1K", "1K-10K", "10K+"]
    bins_counts = [
        int(np.sum(trade_counts == 1)),
        int(np.sum((trade_counts >= 2) & (trade_counts <= 10))),
        int(np.sum((trade_counts >= 11) & (trade_counts <= 100))),
        int(np.sum((trade_counts >= 101) & (trade_counts <= 1000))),
        int(np.sum((trade_counts >= 1001) & (trade_counts <= 10000))),
        int(np.sum(trade_counts > 10000)),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax = axes[0, 0]
    labels = [f"...{a[-6:]}" for a in top20["address"]]
    ax.barh(range(len(top20) - 1, -1, -1), top20["volume_usdc"] / 1e6, color=COLORS["poly"], alpha=0.8)
    ax.set_yticks(range(len(top20) - 1, -1, -1))
    ax.set_yticklabels(labels, fontsize=8, fontfamily="monospace")
    ax.set_xlabel("Volume ($M USDC)")
    ax.set_title("Top 20 Traders by Volume", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)
    ax2 = axes[0, 1]
    plot_step = max(1, len(trader_pct) // 1000)
    plot_idx = np.arange(0, len(trader_pct), plot_step)
    if plot_idx[-1] != len(trader_pct) - 1:
        plot_idx = np.append(plot_idx, len(trader_pct) - 1)
    ax2.plot(trader_pct[plot_idx], cum_vol_pct[plot_idx], color=COLORS["poly"], linewidth=2)
    ax2.plot([0, 100], [0, 100], "--", color=COLORS["neutral"], linewidth=1, alpha=0.5)
    ax2.fill_between(trader_pct[plot_idx], cum_vol_pct[plot_idx], np.linspace(0, 100, len(plot_idx)), alpha=0.15, color=COLORS["poly"])
    ax2.set_xlabel("% of Traders (sorted by volume)")
    ax2.set_ylabel("% of Total Volume")
    ax2.set_title(f"Volume Lorenz Curve  (Gini = {gini:.3f})", fontsize=12, fontweight="bold")
    ax2.grid(alpha=0.3)
    ax3 = axes[1, 0]
    ax3.bar(bins_labels, bins_counts, color=COLORS["accent"], alpha=0.85)
    ax3.set_ylabel("Number of Addresses")
    ax3.set_title("Trader Activity Distribution", fontsize=12, fontweight="bold")
    ax3.set_yscale("log")
    for i, v in enumerate(bins_counts):
        ax3.text(i, v * 1.15, f"{v:,}", ha="center", fontsize=9, color="#e0e0e0")
    ax3.grid(axis="y", alpha=0.3)
    ax4 = axes[1, 1]
    slices = [top100_volume, top10_pct - top100_volume, 100 - top10_pct]
    slice_labels = [f"Top 100\n({top100_volume:.1f}%)", f"Top 10%\n({top10_pct:.1f}%)", f"Rest\n({100 - top10_pct:.1f}%)"]
    colors_pie = [COLORS["danger"], COLORS["accent"], COLORS["neutral"]]
    ax4.pie(slices, labels=slice_labels, colors=colors_pie, autopct="%.1f%%", startangle=140, textprops={"fontsize": 10, "color": "#e0e0e0"}, wedgeprops={"edgecolor": "#0e1117", "linewidth": 1.5})
    ax4.set_title("Volume Concentration", fontsize=12, fontweight="bold")
    fig.tight_layout(pad=2.0)
    _save(fig, "10_whale_tracker.png")
    _save_json("10_whale_tracker.json", {
        "top20_addresses": [a[-8:] for a in top20["address"].tolist()],
        "top20_volume_m": [round(v / 1e6, 2) for v in top20["volume_usdc"]],
        "top20_trades": top20["trade_count"].tolist(),
        "top20_pct_volume": [round(v, 2) for v in top20["pct_volume"]],
        "lorenz_x": lorenz_x,
        "lorenz_y": lorenz_y,
        "gini": round(gini, 4),
        "bins_labels": bins_labels,
        "bins_counts": bins_counts,
        "total_traders": total_traders,
        "total_trades": total_trades,
        "total_volume_m": round(total_volume / 1e6, 1),
        "top1_pct": round(top1_pct, 1),
        "top10_pct": round(top10_pct, 1),
        "top100_pct": round(top100_volume, 1),
    })
    return {"gini": gini, "total_traders": total_traders, "top100_pct": top100_volume}
