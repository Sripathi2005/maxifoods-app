import os
import psycopg2
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

DB_URL = "postgresql://postgres:postgres@localhost:5432/maxifoods"
print("Connecting to PostgreSQL maxifoods database...")
conn = psycopg2.connect(DB_URL)

query = """
SELECT 
    f.order_id,
    c.customer_name,
    c.city AS customer_city,
    r.restaurant_name,
    r.city AS restaurant_city,
    r.primary_cuisine,
    f.order_date,
    f.order_time_slot,
    f.veg_season_tag,
    f.is_veg_order,
    f.item_count,
    f.gross_amount,
    f.discount_pct,
    f.discount_amount,
    f.delivery_fee,
    f.final_amount,
    f.delivery_time_min,
    f.rating_given,
    'CLEANED_DEDUPLICATED' AS etl_status
FROM fact_orders f
LEFT JOIN dim_customer c ON f.customer_id = c.customer_id
LEFT JOIN dim_restaurant r ON f.restaurant_id = r.restaurant_id
ORDER BY f.order_id ASC;
"""

print("Executing SQL join query across fact_orders, dim_customer, and dim_restaurant...")
df = pd.read_sql_query(query, conn)
out_csv = os.path.join(DATA_DIR, "cleaned_maxifoods_orders_dataset.csv")
df.to_csv(out_csv, index=False)
print(f"Successfully generated cleaned dataset with {len(df)} rows across 10 partner restaurants at {out_csv}!")

conn.close()
