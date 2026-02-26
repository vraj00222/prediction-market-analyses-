from pathlib import Path
import duckdb
import matplotlib.pyplot as plt
import json as _json

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "rookie"
CHARTS_DIR = BASE_DIR / "static" / "charts"
CHART_JSON_DIR = BASE_DIR / "static" / "data" / "charts"
for d in (OUTPUT_DIR, CHARTS_DIR, CHART_JSON_DIR):
    d.mkdir(parents=True, exist_ok=True)

KALSHI_TRADES = DATA_DIR / "kalshi" / "trades"
KALSHI_MARKETS = DATA_DIR / "kalshi" / "markets"
POLY_TRADES = DATA_DIR / "polymarket" / "trades"
POLY_MARKETS = DATA_DIR / "polymarket" / "markets"
POLY_BLOCKS = DATA_DIR / "polymarket" / "blocks"

COLORS = {
    "primary": "#4fc3f7",
    "secondary": "#81c784",
    "accent": "#ff8a65",
    "danger": "#ef5350",
    "neutral": "#90a4ae",
    "kalshi": "#818cf8",
    "poly": "#34d399",
}

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

def get_connection():
    return duckdb.connect()

def _save(fig, name):
    for d in (OUTPUT_DIR, CHARTS_DIR):
        fig.savefig(d / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {name}")

def _save_json(filename, data):
    path = CHART_JSON_DIR / filename
    with open(path, "w") as f:
        _json.dump(data, f, separators=(",", ":"))
    print(f"  Saved JSON: {path}")
