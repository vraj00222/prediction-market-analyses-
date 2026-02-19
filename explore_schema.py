"""Quick exploration of all available data."""
import duckdb
import os

con = duckdb.connect()

# Kalshi
print("=== KALSHI TRADES ===")
r = con.sql("SELECT * FROM 'data/kalshi/trades/*.parquet' LIMIT 1")
print(r.columns)
kt = con.sql("SELECT COUNT(*) FROM 'data/kalshi/trades/*.parquet'").fetchone()[0]
print(f"  Rows: {kt:,}")

print("\n=== KALSHI MARKETS ===")
r = con.sql("SELECT * FROM 'data/kalshi/markets/*.parquet' LIMIT 1")
print(r.columns)
km = con.sql("SELECT COUNT(*) FROM 'data/kalshi/markets/*.parquet'").fetchone()[0]
print(f"  Rows: {km:,}")

# Sample Kalshi market categories
print("\n=== KALSHI MARKET EVENT_TICKER PATTERNS (first 20) ===")
cats = con.sql("""
    SELECT 
        REGEXP_REPLACE(event_ticker, '-[0-9T:]+$', '') as category,
        COUNT(*) as cnt
    FROM 'data/kalshi/markets/*.parquet'
    GROUP BY 1
    ORDER BY cnt DESC
    LIMIT 20
""").fetchall()
for c, n in cats:
    print(f"  {c}: {n:,}")

# Sample a Kalshi market row
print("\n=== SAMPLE KALSHI MARKET ===")
print(con.sql("SELECT * FROM 'data/kalshi/markets/*.parquet' LIMIT 3").fetchdf().to_string())

# Polymarket
for table in ["trades", "markets", "legacy_trades"]:
    path = f"data/polymarket/{table}/"
    if os.path.isdir(path):
        files = [f for f in os.listdir(path) if f.endswith(".parquet")]
        if files:
            print(f"\n=== POLYMARKET {table.upper()} ===")
            r = con.sql(f"SELECT * FROM '{path}*.parquet' LIMIT 1")
            print(r.columns)
            cnt = con.sql(f"SELECT COUNT(*) FROM '{path}*.parquet'").fetchone()[0]
            print(f"  Rows: {cnt:,}")

path = "data/polymarket/blocks/"
if os.path.isdir(path):
    files = [f for f in os.listdir(path) if f.endswith(".parquet")]
    if files:
        print(f"\n=== POLYMARKET BLOCKS ===")
        r = con.sql(f"SELECT * FROM '{path}*.parquet' LIMIT 1")
        print(r.columns)
        cnt = con.sql(f"SELECT COUNT(*) FROM '{path}*.parquet'").fetchone()[0]
        print(f"  Rows: {cnt:,}")

# Sample polymarket
poly_trades = "data/polymarket/trades/"
if os.path.isdir(poly_trades):
    files = [f for f in os.listdir(poly_trades) if f.endswith(".parquet")]
    if files:
        print("\n=== SAMPLE POLYMARKET TRADE ===")
        print(con.sql(f"SELECT * FROM '{poly_trades}*.parquet' LIMIT 3").fetchdf().to_string())

poly_markets = "data/polymarket/markets/"
if os.path.isdir(poly_markets):
    files = [f for f in os.listdir(poly_markets) if f.endswith(".parquet")]
    if files:
        print("\n=== SAMPLE POLYMARKET MARKET ===")
        print(con.sql(f"SELECT * FROM '{poly_markets}*.parquet' LIMIT 2").fetchdf().to_string())
