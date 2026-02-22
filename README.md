git clone git@github.com:vraj00222/prediction-market-analyses-.git
pip install -r requirements.txt

# Prediction Market Analysis

A modular, data-driven dashboard for 400M+ prediction market trades from [Kalshi](https://kalshi.com) and [Polymarket](https://polymarket.com).

Built on [Jon Becker's](https://github.com/Jon-Becker/prediction-market-analysis) open dataset.

---

## Features

- Interactive dashboard (Flask + JS + Framer Motion)
- Modular analysis code (each analysis in its own file)
- Platform-based theming (Kalshi/Polymarket)
- API for all data and charts
- Keyboard navigation, responsive design, and more

---

## Project Structure

```
├── app.py                  # Flask server (API + page routes)
├── advanced_analysis.py    # Orchestrates all advanced analyses (modular)
├── analyses/               # Modular analysis code (one file per analysis)
│   ├── __init__.py
│   ├── utils.py            # Shared config/helpers
│   ├── platform_comparison.py
│   ├── whale_tracker.py
│   ├── market_categories.py
│   └── spread_liquidity.py
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── charts/             # Generated chart PNGs
│   └── data/
│       ├── analyses.json   # All analysis metadata
│       └── charts/         # Chart data for Plotly
├── templates/
│   └── index.html
├── requirements.txt / pyproject.toml
├── README.md
```

---

## Quick Start

```bash
git clone git@github.com:vraj00222/prediction-market-analyses-.git
cd prediction-market-analyses-
pip install -r requirements.txt
uv run python app.py
# Open http://localhost:5050
```

---

## Running Analyses

To generate all advanced analyses and charts:

```bash
MPLBACKEND=Agg uv run python advanced_analysis.py
```

- Output PNGs: `output/rookie/` and `static/charts/`
- Output JSONs: `static/data/charts/`

---

## API Endpoints

| Endpoint                  | Description                        |
|---------------------------|------------------------------------|
| `/`                       | Dashboard page                     |
| `/api/data`               | Full dataset (overview + analyses) |
| `/api/overview`           | Top-level stats only               |
| `/api/analyses`           | List of analyses (metadata)        |
| `/api/analysis/<id>`      | Single analysis detail             |
| `/charts/<filename>`      | Chart image                        |
| `/api/chart-data/<file>`  | Chart JSON for Plotly              |

---

## Tech Stack

- **Backend:** Flask, DuckDB, Matplotlib
- **Frontend:** Vanilla JS, Framer Motion, CSS custom properties
- **Data:** Apache Parquet via DuckDB

---

## License

MIT
