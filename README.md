# Prediction Market Analysis

A data-driven analysis dashboard for 400M+ prediction market trades from [Kalshi](https://kalshi.com) and [Polymarket](https://polymarket.com).

Built on [Jon Becker's](https://github.com/Jon-Becker/prediction-market-analysis) open dataset.

## Analyses

| # | Analysis | What it reveals |
|---|----------|-----------------|
| 1 | **Dataset Overview** | Platform growth, volume trends, market resolution stats |
| 2 | **Calibration Curve** | Whether market prices actually reflect true probabilities |
| 3 | **Longshot Bias** | Cheap contracts are systematically overpriced |
| 4 | **Maker vs Taker** | Passive liquidity providers win; takers lose ~$143M |
| 5 | **Trade Size Distribution** | Fat-tailed sizing — top 2.4% of trades = 50% of volume |
| 6 | **Returns by Hour** | Time-of-day patterns in taker excess returns |
| 7 | **Calibration Surface** | 2D heatmap of mispricing by price x time-to-close |
| 8 | **Monte Carlo Kelly** | Risk sizing under uncertainty with resampled outcomes |

## Quick Start

```bash
# Clone
git clone git@github.com:vraj00222/prediction-market-analyses-.git
cd prediction-market-analyses-

# Install dependencies (requires Python 3.11+)
pip install -r requirements.txt

# Run the web dashboard
python app.py          # or: uv run python app.py (if using uv)
# Open http://localhost:5050
```

## Generating Fresh Charts

The repo includes pre-generated charts. To regenerate from raw data:

1. Download the dataset (~36 GB) — see [Jon Becker's repo](https://github.com/Jon-Becker/prediction-market-analysis) for instructions
2. Place data in `data/kalshi/{trades,markets}/`
3. Run:

```bash
MPLBACKEND=Agg python rookie_analysis.py
```

Charts are saved to `static/charts/` and `output/rookie/`.

## Project Structure

```
├── app.py                  # Flask server (API + page routes)
├── rookie_analysis.py      # DuckDB analysis script (generates charts)
├── requirements.txt        # Python dependencies
├── README.md
├── static/
│   ├── css/style.css       # Dark theme + animations
│   ├── js/app.js           # SPA logic (Framer Motion)
│   ├── charts/             # 8 pre-generated chart PNGs
│   └── data/
│       └── analyses.json   # All analysis data + learn sections
└── templates/
    └── index.html          # HTML shell (loads CSS/JS/Motion CDN)
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard page |
| `GET /api/data` | Full dataset (overview + all analyses) |
| `GET /api/overview` | Top-level stats only |
| `GET /api/analyses` | List of analyses (metadata) |
| `GET /api/analysis/<id>` | Single analysis detail |
| `GET /charts/<filename>` | Chart image |

## Tech Stack

- **Backend:** Flask, DuckDB, Matplotlib
- **Frontend:** Vanilla JS + [Framer Motion](https://motion.dev) (animation), CSS custom properties
- **Data:** Apache Parquet via DuckDB

## Features

- Dark-theme dashboard with smooth Framer Motion animations
- Collapsible "Learn" sections with beginner-friendly explanations & key term glossaries
- Keyboard navigation (arrow keys) between analyses
- Responsive grid layout (desktop → tablet → mobile)
- Cursor-glow ambient light effect

## Dataset Stats

- **72.1M** trades on Kalshi (Jun 2021 - Nov 2025)
- **18.3B** contracts traded
- **586K** unique markets
- **7.3M** resolved markets

## License

MIT
