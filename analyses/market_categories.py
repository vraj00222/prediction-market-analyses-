from analyses.utils import get_connection, _save, _save_json, COLORS, KALSHI_MARKETS
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def market_categories():
    """Classify Kalshi markets by event type and analyze volume by category."""
    con = get_connection()
    cat_data = con.sql(f"""
        WITH categorized AS (
            SELECT m.ticker, m.event_ticker, m.title, m.volume, m.result, m.created_time,
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
        SELECT category, COUNT(*) AS market_count, SUM(volume) AS total_volume, AVG(volume) AS avg_volume, COUNT(CASE WHEN result IS NOT NULL AND result != '' THEN 1 END) AS settled_count
        FROM categorized
        GROUP BY 1
        ORDER BY total_volume DESC
    """).fetchdf()
    monthly_cats = con.sql(f"""
        WITH categorized AS (
            SELECT DATE_TRUNC('month', created_time) AS month,
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
    pivot = monthly_cats.pivot_table(index="month", columns="category", values="cnt", fill_value=0)
    col_order = pivot.sum().sort_values(ascending=False).index.tolist()
    pivot = pivot[col_order]
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    cat_colors = {
        "Sports": "#818cf8", "Politics": "#ef5350", "Crypto": "#fbbf24",
        "Weather": "#60a5fa", "Economy & Finance": "#34d399",
        "Entertainment": "#f472b6", "Health": "#a78bfa", "Tech": "#22d3ee",
        "Other": "#6b7280"
    }
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
        ax.text(row["total_volume"] / 1e6 + 0.5, i, f'{row["market_count"]:,} mkts', va="center", fontsize=9, color="#aaa")
    ax.grid(axis="x", alpha=0.3)
    ax2 = axes[1]
    months = pivot.index
    bottom = np.zeros(len(months))
    for col in col_order[:6]:
        vals = pivot[col].values.astype(float)
        ax2.fill_between(months, bottom, bottom + vals, alpha=0.7, color=cat_colors.get(col, COLORS["neutral"]), label=col)
        bottom += vals
    ax2.set_ylabel("Markets Created")
    ax2.set_title("Monthly Market Creation by Category", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(axis="y", alpha=0.3)
    fig.tight_layout(pad=2.0)
    _save(fig, "11_market_categories.png")
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
