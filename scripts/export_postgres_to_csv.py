import os
import psycopg2
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_URL = "postgresql://postgres:postgres@localhost:5432/maxifoods"

print(f"Connecting to PostgreSQL 'maxifoods' database and exporting to {DATA_DIR}...")
conn = psycopg2.connect(DB_URL)

tables = ["dim_customer", "dim_restaurant", "dim_food_item", "dim_time", "fact_orders", "fact_order_items"]

for table in tables:
    df = pd.read_sql_query(f'SELECT * FROM "{table}"', conn)
    csv_path = os.path.join(DATA_DIR, f"{table}.csv")
    df.to_csv(csv_path, index=False)
    print(f" -> Exported '{table}': {len(df)} rows saved to {csv_path}")

conn.close()
print("\nAll PostgreSQL tables successfully exported to project data/ folder!")
