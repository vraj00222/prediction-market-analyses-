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

# Install dependencies
pip install -r requirements.txt

# Run the web dashboard
python app.py
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
├── app.py                  # Flask server (API + page serving)
├── rookie_analysis.py      # Analysis script (generates charts + data)
├── requirements.txt        # Python dependencies
├── static/
│   ├── css/style.css       # Dashboard styles
│   ├── js/app.js           # Dynamic frontend (SPA)
│   ├── charts/             # Generated chart PNGs
│   └── data/
│       └── analyses.json   # Analysis metadata & stats
└── templates/
    └── index.html          # HTML shell
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
- **Frontend:** Vanilla JS (no framework), CSS custom properties
- **Data:** Apache Parquet via DuckDB

## Dataset Stats

- **72.1M** trades on Kalshi (Jun 2021 - Nov 2025)
- **18.3B** contracts traded
- **586K** unique markets
- **7.3M** resolved markets

## License

MIT
