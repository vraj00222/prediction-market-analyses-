"""
Advanced Prediction Market Analyses (9–12)
------------------------------------------
Modularized runner for all advanced analyses.

Usage:
  cd prediction-market-analysis
  MPLBACKEND=Agg uv run python advanced_analysis.py

Output: PNGs → output/rookie/ + static/charts/
        JSONs → static/data/charts/
"""

from analyses.platform_comparison import platform_comparison
from analyses.whale_tracker import whale_tracker
from analyses.market_categories import market_categories
from analyses.spread_liquidity import spread_liquidity

if __name__ == "__main__":
    print("\n🔬 Running Advanced Analyses (9–12)...\n")
    r9 = platform_comparison()
    r10 = whale_tracker()
    r11 = market_categories()
    r12 = spread_liquidity()
    print("\n" + "=" * 60)
    print("  ✅ ALL ADVANCED ANALYSES COMPLETE")
    print("=" * 60)
    print(f"  PNGs → output/rookie/")
    print(f"  PNGs → static/charts/")
    print(f"  JSONs → static/data/charts/")

# ══════════════════════════════════════════════════════════════════════════════
#  10. WHALE TRACKER — Polymarket Address Concentration
# ══════════════════════════════════════════════════════════════════════════════
def analysis_10_whale_tracker():
    """Analyze trading concentration by Polymarket address."""
    print("\n" + "=" * 60)
    print("  10/12  WHALE TRACKER (POLYMARKET)")
    print("=" * 60)

    con = get_connection()

    print("  Querying trader activity (this may take several minutes)...")
    # Get trade counts and volume per unique address (using taker as the active trader)
    trader_stats = con.sql(f"""
        SELECT
            taker AS address,
            COUNT(*) AS trade_count,
            SUM(CAST(taker_amount AS DOUBLE) / 1e6) AS volume_usdc
        FROM '{POLY_TRADES}/*.parquet'
        GROUP BY 1
        ORDER BY volume_usdc DESC
    """).fetchdf()

    total_traders = len(trader_stats)
    total_trades = int(trader_stats["trade_count"].sum())
    total_volume = float(trader_stats["volume_usdc"].sum())

    print(f"  Unique taker addresses: {total_traders:,}")
    print(f"  Total trades: {total_trades:,}")
    print(f"  Total volume: ${total_volume:,.0f} USDC")

    # Top 20 traders
    top20 = trader_stats.head(20).copy()
    top20["pct_volume"] = top20["volume_usdc"] / total_volume * 100

    # Concentration metrics
    top1_pct = trader_stats.head(max(1, total_traders // 100))["volume_usdc"].sum() / total_volume * 100
    top10_pct = trader_stats.head(max(1, total_traders // 10))["volume_usdc"].sum() / total_volume * 100
    top100_volume = trader_stats.head(100)["volume_usdc"].sum() / total_volume * 100

    print(f"  Top 1% of addresses: {top1_pct:.1f}% of volume")
    print(f"  Top 10% of addresses: {top10_pct:.1f}% of volume")
    print(f"  Top 100 addresses: {top100_volume:.1f}% of volume")

    # Lorenz curve (volume concentration)
    sorted_vol = np.sort(trader_stats["volume_usdc"].values)
    cum_vol = np.cumsum(sorted_vol)
    cum_vol_pct = cum_vol / cum_vol[-1] * 100
    trader_pct = np.arange(1, len(sorted_vol) + 1) / len(sorted_vol) * 100

    # Downsample Lorenz for JSON (take every nth point + boundaries)
    n = len(trader_pct)
    step = max(1, n // 200)
    idx = list(range(0, n, step))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    lorenz_x = [round(trader_pct[i], 2) for i in idx]
    lorenz_y = [round(cum_vol_pct[i], 2) for i in idx]

    # Gini coefficient
    n_g = len(sorted_vol)
    gini = (2 * np.sum(np.arange(1, n_g + 1) * sorted_vol) - (n_g + 1) * np.sum(sorted_vol)) / (n_g * np.sum(sorted_vol))

    print(f"  Gini coefficient: {gini:.4f}")

    # Trade count distribution (log bins)
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

    # ── Plot ──
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top-left: Top 20 by volume (horizontal bar)
    ax = axes[0, 0]
    labels = [f"...{a[-6:]}" for a in top20["address"]]
    ax.barh(range(len(top20) - 1, -1, -1), top20["volume_usdc"] / 1e6, color=COLORS["poly"], alpha=0.8)
    ax.set_yticks(range(len(top20) - 1, -1, -1))
    ax.set_yticklabels(labels, fontsize=8, fontfamily="monospace")
    ax.set_xlabel("Volume ($M USDC)")
    ax.set_title("Top 20 Traders by Volume", fontsize=12, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    # Top-right: Lorenz curve (downsample for plotting — 1.9M points is too many)
    ax2 = axes[0, 1]
    plot_step = max(1, len(trader_pct) // 1000)
    plot_idx = np.arange(0, len(trader_pct), plot_step)
    if plot_idx[-1] != len(trader_pct) - 1:
        plot_idx = np.append(plot_idx, len(trader_pct) - 1)
    ax2.plot(trader_pct[plot_idx], cum_vol_pct[plot_idx], color=COLORS["poly"], linewidth=2)
    ax2.plot([0, 100], [0, 100], "--", color=COLORS["neutral"], linewidth=1, alpha=0.5)
    ax2.fill_between(trader_pct[plot_idx], cum_vol_pct[plot_idx],
                     np.linspace(0, 100, len(plot_idx)), alpha=0.15, color=COLORS["poly"])
    ax2.set_xlabel("% of Traders (sorted by volume)")
    ax2.set_ylabel("% of Total Volume")
    ax2.set_title(f"Volume Lorenz Curve  (Gini = {gini:.3f})", fontsize=12, fontweight="bold")
    ax2.grid(alpha=0.3)

    # Bottom-left: Trader activity distribution
    ax3 = axes[1, 0]
    ax3.bar(bins_labels, bins_counts, color=COLORS["accent"], alpha=0.85)
    ax3.set_ylabel("Number of Addresses")
    ax3.set_title("Trader Activity Distribution", fontsize=12, fontweight="bold")
    ax3.set_yscale("log")
    for i, v in enumerate(bins_counts):
        ax3.text(i, v * 1.15, f"{v:,}", ha="center", fontsize=9, color="#e0e0e0")
    ax3.grid(axis="y", alpha=0.3)

    # Bottom-right: Concentration pie
    ax4 = axes[1, 1]
    slices = [top100_volume, top10_pct - top100_volume / total_volume, 100 - top10_pct]
    slice_labels = [f"Top 100\n({top100_volume:.1f}%)", f"Top 10%\n({top10_pct:.1f}%)", f"Rest\n({100 - top10_pct:.1f}%)"]
    colors_pie = [COLORS["danger"], COLORS["accent"], COLORS["neutral"]]
    wedges, texts, autotexts = ax4.pie(
        [top100_volume, top10_pct - top100_volume, 100 - top10_pct],
        labels=slice_labels, colors=colors_pie, autopct="%.1f%%",
        startangle=140, textprops={"fontsize": 10, "color": "#e0e0e0"},
        wedgeprops={"edgecolor": "#0e1117", "linewidth": 1.5}
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax4.set_title("Volume Concentration", fontsize=12, fontweight="bold")

    fig.tight_layout(pad=2.0)
    _save(fig, "10_whale_tracker.png")

    # ── JSON ──
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


# ══════════════════════════════════════════════════════════════════════════════
#  11. MARKET CATEGORIES — What Do People Bet On?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_11_market_categories():
    """Classify Kalshi markets by event type and analyze volume by category."""
    print("\n" + "=" * 60)
    print("  11/12  MARKET CATEGORIES (KALSHI)")
    print("=" * 60)

    con = get_connection()

    print("  Querying market volumes by category...")
    # Parse event_ticker to extract category prefixes
    cat_data = con.sql(f"""
        WITH categorized AS (
            SELECT
                m.ticker,
                m.event_ticker,
                m.title,
                m.volume,
                m.result,
                m.created_time,
                CASE
                    WHEN UPPER(m.event_ticker) LIKE '%NFL%' OR UPPER(m.event_ticker) LIKE '%NBA%'
                         OR UPPER(m.event_ticker) LIKE '%MLB%' OR UPPER(m.event_ticker) LIKE '%NHL%'
                         OR UPPER(m.event_ticker) LIKE '%SPORTS%' OR UPPER(m.event_ticker) LIKE '%SOCCER%'
                         OR UPPER(m.event_ticker) LIKE '%UFC%' OR UPPER(m.event_ticker) LIKE '%TENNIS%'
                         OR UPPER(m.event_ticker) LIKE '%GOLF%' OR UPPER(m.event_ticker) LIKE '%F1%'
                         OR UPPER(m.event_ticker) LIKE '%SINGLEGAME%' OR UPPER(m.event_ticker) LIKE '%MULTIGAME%'
                         OR UPPER(m.event_ticker) LIKE '%SUPER%BOWL%' THEN 'Sports'
                    WHEN UPPER(m.event_ticker) LIKE '%ELECT%' OR UPPER(m.event_ticker) LIKE '%TRUMP%'
                         OR UPPER(m.event_ticker) LIKE '%BIDEN%' OR UPPER(m.event_ticker) LIKE '%PRES%'
                         OR UPPER(m.event_ticker) LIKE '%CONGRESS%' OR UPPER(m.event_ticker) LIKE '%SENATE%'
                         OR UPPER(m.event_ticker) LIKE '%GOVERNOR%' OR UPPER(m.event_ticker) LIKE '%PARTY%'
                         OR UPPER(m.event_ticker) LIKE '%DEM%' OR UPPER(m.event_ticker) LIKE '%GOP%'
                         OR UPPER(m.event_ticker) LIKE '%HARRIS%' OR UPPER(m.event_ticker) LIKE '%VOTE%'
                         THEN 'Politics'
                    WHEN UPPER(m.event_ticker) LIKE '%CRYPTO%' OR UPPER(m.event_ticker) LIKE '%BTC%'
                         OR UPPER(m.event_ticker) LIKE '%ETH%' OR UPPER(m.event_ticker) LIKE '%BITCOIN%'
                         OR UPPER(m.event_ticker) LIKE '%SOL%' THEN 'Crypto'
                    WHEN UPPER(m.event_ticker) LIKE '%WEATHER%' OR UPPER(m.event_ticker) LIKE '%TEMP%'
                         OR UPPER(m.event_ticker) LIKE '%HURRICANE%' OR UPPER(m.event_ticker) LIKE '%RAIN%'
                         OR UPPER(m.event_ticker) LIKE '%SNOW%' OR UPPER(m.event_ticker) LIKE '%CLIMATE%'
                         THEN 'Weather'
                    WHEN UPPER(m.event_ticker) LIKE '%ECON%' OR UPPER(m.event_ticker) LIKE '%GDP%'
                         OR UPPER(m.event_ticker) LIKE '%CPI%' OR UPPER(m.event_ticker) LIKE '%JOBS%'
                         OR UPPER(m.event_ticker) LIKE '%FOMC%' OR UPPER(m.event_ticker) LIKE '%FED%'
                         OR UPPER(m.event_ticker) LIKE '%RATE%' OR UPPER(m.event_ticker) LIKE '%INFLATION%'
                         OR UPPER(m.event_ticker) LIKE '%TREASURY%' OR UPPER(m.event_ticker) LIKE '%SP500%'
                         OR UPPER(m.event_ticker) LIKE '%NASDAQ%' OR UPPER(m.event_ticker) LIKE '%STOCK%'
                         THEN 'Economy & Finance'
                    WHEN UPPER(m.event_ticker) LIKE '%OSCAR%' OR UPPER(m.event_ticker) LIKE '%GRAMMY%'
                         OR UPPER(m.event_ticker) LIKE '%EMMY%' OR UPPER(m.event_ticker) LIKE '%MENTION%'
                         OR UPPER(m.event_ticker) LIKE '%TWITTER%' OR UPPER(m.event_ticker) LIKE '%CELEB%'
                         OR UPPER(m.event_ticker) LIKE '%MOVIE%' OR UPPER(m.event_ticker) LIKE '%MUSIC%'
                         THEN 'Entertainment'
                    WHEN UPPER(m.event_ticker) LIKE '%COVID%' OR UPPER(m.event_ticker) LIKE '%VIRUS%'
                         OR UPPER(m.event_ticker) LIKE '%HEALTH%' OR UPPER(m.event_ticker) LIKE '%FDA%'
                         THEN 'Health'
                    WHEN UPPER(m.event_ticker) LIKE '%TECH%' OR UPPER(m.event_ticker) LIKE '%AI%'
                         OR UPPER(m.event_ticker) LIKE '%APPLE%' OR UPPER(m.event_ticker) LIKE '%GOOGLE%'
                         OR UPPER(m.event_ticker) LIKE '%TSLA%' OR UPPER(m.event_ticker) LIKE '%META%'
                         THEN 'Tech'
                    ELSE 'Other'
                END AS category
            FROM '{KALSHI_MARKETS}/*.parquet' m
        )
        SELECT
            category,
            COUNT(*) AS market_count,
            SUM(volume) AS total_volume,
            AVG(volume) AS avg_volume,
            COUNT(CASE WHEN result IS NOT NULL AND result != '' THEN 1 END) AS settled_count
        FROM categorized
        GROUP BY 1
        ORDER BY total_volume DESC
    """).fetchdf()

    # Monthly category distribution
    print("  Querying monthly category breakdown...")
    monthly_cats = con.sql(f"""
        WITH categorized AS (
            SELECT
                DATE_TRUNC('month', created_time) AS month,
                CASE
                    WHEN UPPER(event_ticker) LIKE '%NFL%' OR UPPER(event_ticker) LIKE '%NBA%'
                         OR UPPER(event_ticker) LIKE '%MLB%' OR UPPER(event_ticker) LIKE '%NHL%'
                         OR UPPER(event_ticker) LIKE '%SPORTS%' OR UPPER(event_ticker) LIKE '%SINGLEGAME%'
                         OR UPPER(event_ticker) LIKE '%MULTIGAME%' OR UPPER(event_ticker) LIKE '%UFC%'
                         THEN 'Sports'
                    WHEN UPPER(event_ticker) LIKE '%ELECT%' OR UPPER(event_ticker) LIKE '%TRUMP%'
                         OR UPPER(event_ticker) LIKE '%BIDEN%' OR UPPER(event_ticker) LIKE '%PRES%'
                         OR UPPER(event_ticker) LIKE '%CONGRESS%' OR UPPER(event_ticker) LIKE '%SENATE%'
                         OR UPPER(event_ticker) LIKE '%HARRIS%' OR UPPER(event_ticker) LIKE '%VOTE%'
                         THEN 'Politics'
                    WHEN UPPER(event_ticker) LIKE '%CRYPTO%' OR UPPER(event_ticker) LIKE '%BTC%'
                         OR UPPER(event_ticker) LIKE '%ETH%' OR UPPER(event_ticker) LIKE '%BITCOIN%'
                         THEN 'Crypto'
                    WHEN UPPER(event_ticker) LIKE '%WEATHER%' OR UPPER(event_ticker) LIKE '%TEMP%'
                         OR UPPER(event_ticker) LIKE '%HURRICANE%' THEN 'Weather'
                    WHEN UPPER(event_ticker) LIKE '%ECON%' OR UPPER(event_ticker) LIKE '%GDP%'
                         OR UPPER(event_ticker) LIKE '%CPI%' OR UPPER(event_ticker) LIKE '%FED%'
                         OR UPPER(event_ticker) LIKE '%RATE%' OR UPPER(event_ticker) LIKE '%SP500%'
                         OR UPPER(event_ticker) LIKE '%NASDAQ%' THEN 'Economy & Finance'
                    WHEN UPPER(event_ticker) LIKE '%OSCAR%' OR UPPER(event_ticker) LIKE '%GRAMMY%'
                         OR UPPER(event_ticker) LIKE '%MENTION%' THEN 'Entertainment'
                    ELSE 'Other'
                END AS category
            FROM '{KALSHI_MARKETS}/*.parquet'
            WHERE created_time IS NOT NULL
        )
        SELECT month, category, COUNT(*) AS cnt
        FROM categorized
        GROUP BY 1, 2
        ORDER BY 1, 2
    """).fetchdf()

    # Pivot for stacked area
    pivot = monthly_cats.pivot_table(index="month", columns="category", values="cnt", fill_value=0)
    # Sort columns by total
    col_order = pivot.sum().sort_values(ascending=False).index.tolist()
    pivot = pivot[col_order]

    print(f"  Categories found: {len(cat_data)}")
    for _, row in cat_data.iterrows():
        print(f"    {row['category']}: {row['market_count']:,} markets, {row['total_volume']:,.0f} volume")

    # ── Plot ──
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))

    cat_colors = {
        "Sports": "#818cf8", "Politics": "#ef5350", "Crypto": "#fbbf24",
        "Weather": "#60a5fa", "Economy & Finance": "#34d399",
        "Entertainment": "#f472b6", "Health": "#a78bfa", "Tech": "#22d3ee",
        "Other": "#6b7280"
    }

    # Left: Treemap-style horizontal bars
    ax = axes[0]
    sorted_cats = cat_data.sort_values("total_volume", ascending=True)
    y_pos = range(len(sorted_cats))
    bar_colors = [cat_colors.get(c, COLORS["neutral"]) for c in sorted_cats["category"]]
    ax.barh(y_pos, sorted_cats["total_volume"] / 1e6, color=bar_colors, alpha=0.85)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_cats["category"], fontsize=10)
    ax.set_xlabel("Total Volume (millions of contracts)")
    ax.set_title("Volume by Market Category", fontsize=13, fontweight="bold")
    for i, (_, row) in enumerate(sorted_cats.iterrows()):
        ax.text(row["total_volume"] / 1e6 + 0.5, i, f'{row["market_count"]:,} mkts',
                va="center", fontsize=9, color="#aaa")
    ax.grid(axis="x", alpha=0.3)

    # Right: Stacked area over time
    ax2 = axes[1]
    months = pivot.index
    bottom = np.zeros(len(months))
    for col in col_order[:6]:  # top 6 categories
        vals = pivot[col].values.astype(float)
        ax2.fill_between(months, bottom, bottom + vals, alpha=0.7,
                         color=cat_colors.get(col, COLORS["neutral"]), label=col)
        bottom += vals
    ax2.set_ylabel("Markets Created")
    ax2.set_title("Monthly Market Creation by Category", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(axis="y", alpha=0.3)

    fig.tight_layout(pad=2.0)
    _save(fig, "11_market_categories.png")

    # ── JSON ──
    categories = cat_data["category"].tolist()
    _save_json("11_market_categories.json", {
        "categories": categories,
        "market_count": cat_data["market_count"].tolist(),
        "total_volume_m": [round(v / 1e6, 2) for v in cat_data["total_volume"]],
        "avg_volume": [round(v, 0) for v in cat_data["avg_volume"]],
        "settled_count": cat_data["settled_count"].tolist(),
        "monthly_months": [str(d.date()) for d in pivot.index],
        "monthly_stacks": {col: pivot[col].tolist() for col in col_order[:6]},
        "cat_colors": {c: cat_colors.get(c, COLORS["neutral"]) for c in categories},
    })

    return cat_data


# ══════════════════════════════════════════════════════════════════════════════
#  12. SPREAD & LIQUIDITY — Kalshi Bid-Ask Spread Analysis
# ══════════════════════════════════════════════════════════════════════════════
def analysis_12_spread_liquidity():
    """Analyze bid-ask spreads on Kalshi, their relationship to volume and time-to-expiry."""
    print("\n" + "=" * 60)
    print("  12/12  SPREAD & LIQUIDITY (KALSHI)")
    print("=" * 60)

    con = get_connection()

    print("  Querying spread data...")
    spread_data = con.sql(f"""
        SELECT
            yes_bid, yes_ask, no_bid, no_ask,
            volume, open_interest, last_price,
            EXTRACT(EPOCH FROM (close_time - created_time)) / 3600.0 AS hours_to_close,
            result
        FROM '{KALSHI_MARKETS}/*.parquet'
        WHERE yes_bid > 0 AND yes_ask > 0
          AND yes_ask > yes_bid
          AND close_time > created_time
    """).fetchdf()

    spread_data["spread"] = spread_data["yes_ask"] - spread_data["yes_bid"]
    spread_data["mid"] = (spread_data["yes_ask"] + spread_data["yes_bid"]) / 2

    total_markets = len(spread_data)
    avg_spread = spread_data["spread"].mean()
    median_spread = spread_data["spread"].median()

    print(f"  Markets with valid spreads: {total_markets:,}")
    print(f"  Average spread: {avg_spread:.1f}¢")
    print(f"  Median spread: {median_spread:.0f}¢")

    # Spread distribution
    spread_hist = np.histogram(spread_data["spread"].clip(0, 50), bins=50)
    hist_counts = spread_hist[0].tolist()
    hist_edges = [round(e, 1) for e in spread_hist[1].tolist()]

    # Spread vs volume (bin by volume deciles)
    spread_data["vol_bin"] = pd.qcut(spread_data["volume"].clip(lower=1), q=10, duplicates="drop")
    vol_spread = spread_data.groupby("vol_bin", observed=True).agg(
        avg_spread=("spread", "mean"),
        median_spread=("spread", "median"),
        count=("spread", "count"),
        avg_volume=("volume", "mean"),
    ).reset_index()

    # Spread vs time to close
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

    # Spread vs mid price
    spread_data["price_bucket"] = (spread_data["mid"] / 5).round() * 5
    price_spread = spread_data.groupby("price_bucket", observed=True).agg(
        avg_spread=("spread", "mean"),
        count=("spread", "count"),
    ).reset_index()
    price_spread = price_spread[(price_spread["price_bucket"] >= 5) & (price_spread["price_bucket"] <= 95)]

    # ── Plot ──
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Top-left: Spread distribution
    ax = axes[0, 0]
    ax.bar([(hist_edges[i] + hist_edges[i + 1]) / 2 for i in range(len(hist_counts))],
           hist_counts, width=1, color=COLORS["primary"], alpha=0.8)
    ax.axvline(avg_spread, color=COLORS["accent"], linestyle="--", label=f"Mean: {avg_spread:.1f}¢")
    ax.axvline(median_spread, color=COLORS["secondary"], linestyle="--", label=f"Median: {median_spread:.0f}¢")
    ax.set_xlabel("Bid-Ask Spread (¢)")
    ax.set_ylabel("Number of Markets")
    ax.set_title("Spread Distribution", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    # Top-right: Spread vs volume
    ax2 = axes[0, 1]
    ax2.plot(vol_spread["avg_volume"], vol_spread["avg_spread"], "o-",
             color=COLORS["primary"], markersize=8, linewidth=2)
    ax2.set_xlabel("Average Volume (contracts)")
    ax2.set_ylabel("Average Spread (¢)")
    ax2.set_title("Spread vs Volume", fontsize=12, fontweight="bold")
    ax2.set_xscale("log")
    ax2.grid(alpha=0.3)

    # Bottom-left: Spread vs time to close
    ax3 = axes[1, 0]
    x_pos = range(len(time_spread))
    ax3.bar(x_pos, time_spread["avg_spread"], color=COLORS["accent"], alpha=0.85)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(time_spread["hours_bin"], fontsize=10)
    ax3.set_ylabel("Average Spread (¢)")
    ax3.set_title("Spread vs Time to Close", fontsize=12, fontweight="bold")
    for i, row in time_spread.iterrows():
        ax3.text(list(x_pos)[i], row["avg_spread"] + 0.3, f'{row["count"]:,}',
                 ha="center", fontsize=8, color="#999")
    ax3.grid(axis="y", alpha=0.3)

    # Bottom-right: Spread vs mid price (smile pattern)
    ax4 = axes[1, 1]
    ax4.plot(price_spread["price_bucket"], price_spread["avg_spread"], "o-",
             color=COLORS["secondary"], markersize=6, linewidth=2)
    ax4.set_xlabel("Mid Price (¢)")
    ax4.set_ylabel("Average Spread (¢)")
    ax4.set_title("Spread vs Price (Liquidity Smile)", fontsize=12, fontweight="bold")
    ax4.grid(alpha=0.3)

    fig.tight_layout(pad=2.0)
    _save(fig, "12_spread_liquidity.png")

    # ── JSON ──
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


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n🔬 Running Advanced Analyses (9–12)...\n")

    r9 = analysis_9_platform_comparison()
    r10 = analysis_10_whale_tracker()
    r11 = analysis_11_market_categories()
    r12 = analysis_12_spread_liquidity()

    print("\n" + "=" * 60)
    print("  ✅ ALL ADVANCED ANALYSES COMPLETE")
    print("=" * 60)
    print(f"  PNGs → {OUTPUT_DIR}/")
    print(f"  PNGs → {CHARTS_DIR}/")
    print(f"  JSONs → {CHART_JSON_DIR}/")
