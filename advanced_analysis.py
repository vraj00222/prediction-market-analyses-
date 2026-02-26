"""Advanced Prediction Market Analyses (9–12)

Usage:
  cd prediction-market-analysis
  MPLBACKEND=Agg uv run python advanced_analysis.py

Output:
  PNGs → output/rookie/ + static/charts/
  JSONs → static/data/charts/
"""

from analyses.platform_comparison import platform_comparison
from analyses.whale_tracker import whale_tracker
from analyses.market_categories import market_categories
from analyses.spread_liquidity import spread_liquidity

if __name__ == "__main__":
    print("\nRunning Advanced Analyses (9–12)...\n")
    platform_comparison()
    whale_tracker()
    market_categories()
    spread_liquidity()
    print("\n" + "=" * 60)
    print("  ALL ADVANCED ANALYSES COMPLETE")
    print("=" * 60)
    print("  PNGs → output/rookie/ + static/charts/")
    print("  JSONs → static/data/charts/")
