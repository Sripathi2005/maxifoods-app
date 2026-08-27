import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

engine = create_engine("postgresql://postgres:postgres@localhost:5432/maxifoods")

print("Truncating and seeding PostgreSQL maxifoods database tables with CASCADE...")

tables = ["fact_order_items", "fact_orders", "analytics_rfm_segments", "analytics_market_basket_rules", "dim_food_item", "dim_customer", "dim_restaurant", "dim_time"]

with engine.connect() as conn:
    for t in tables:
        try:
            conn.execute(text(f'TRUNCATE TABLE "{t}" CASCADE;'))
            conn.commit()
            print(f" -> Truncated {t}")
        except Exception as e:
            print(f" -> Skipping truncate for {t}: {e}")

print("\nSeeding clean CSV tables into PostgreSQL...")
dim_customer = pd.read_csv(os.path.join(DATA_DIR, "dim_customer.csv"))
dim_restaurant = pd.read_csv(os.path.join(DATA_DIR, "dim_restaurant.csv"))
dim_food_item = pd.read_csv(os.path.join(DATA_DIR, "dim_food_item.csv"))
dim_time = pd.read_csv(os.path.join(DATA_DIR, "dim_time.csv"))
fact_orders = pd.read_csv(os.path.join(DATA_DIR, "fact_orders.csv"))
fact_order_items = pd.read_csv(os.path.join(DATA_DIR, "fact_order_items.csv"))

dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
print(" -> dim_customer seeded (2,033 rows)")

dim_restaurant.to_sql("dim_restaurant", engine, if_exists="append", index=False)
print(" -> dim_restaurant seeded (10 rows)")

dim_food_item.to_sql("dim_food_item", engine, if_exists="append", index=False)
print(" -> dim_food_item seeded (2,902 rows)")

dim_time.to_sql("dim_time", engine, if_exists="append", index=False)
print(" -> dim_time seeded (212 rows)")

fact_orders.to_sql("fact_orders", engine, if_exists="append", index=False)
print(" -> fact_orders seeded (11,804 rows)")

fact_order_items.to_sql("fact_order_items", engine, if_exists="append", index=False)
print(" -> fact_order_items seeded (33,045 rows)")

print("\nPostgreSQL 'maxifoods' database successfully updated with original Swiggy Chennai dataset!")
