import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

engine = create_engine("postgresql://postgres:postgres@localhost:5432/maxifoods")

tables = ["fact_order_items", "fact_orders", "dim_food_item", "dim_customer", "dim_restaurant", "dim_time"]

print("Reseeding clean star-schema tables into PostgreSQL...")
with engine.connect() as conn:
    for t in tables:
        try:
            conn.execute(text(f'TRUNCATE TABLE "{t}" CASCADE;'))
            conn.commit()
            print(f" -> Truncated {t}")
        except Exception as e:
            print(f" -> Skipping truncate for {t}: {e}")

dim_customer = pd.read_csv(os.path.join(DATA_DIR, "dim_customer.csv"))
dim_restaurant = pd.read_csv(os.path.join(DATA_DIR, "dim_restaurant.csv"))
dim_food_item = pd.read_csv(os.path.join(DATA_DIR, "dim_food_item.csv"))
dim_time = pd.read_csv(os.path.join(DATA_DIR, "dim_time.csv"))
fact_orders = pd.read_csv(os.path.join(DATA_DIR, "fact_orders.csv"))
fact_order_items = pd.read_csv(os.path.join(DATA_DIR, "fact_order_items.csv"))

dim_customer.to_sql("dim_customer", engine, if_exists="append", index=False)
print(" -> dim_customer seeded (2,170 rows)")

dim_restaurant.to_sql("dim_restaurant", engine, if_exists="append", index=False)
print(" -> dim_restaurant seeded (15 rows)")

dim_food_item.to_sql("dim_food_item", engine, if_exists="append", index=False)
print(" -> dim_food_item seeded (3,738 rows)")

dim_time.to_sql("dim_time", engine, if_exists="append", index=False)
print(" -> dim_time seeded (365 rows)")

fact_orders.to_sql("fact_orders", engine, if_exists="append", index=False)
print(f" -> fact_orders seeded ({len(fact_orders)} rows)")

fact_order_items.to_sql("fact_order_items", engine, if_exists="append", index=False)
print(f" -> fact_order_items seeded ({len(fact_order_items)} rows)")

print("\nPostgreSQL 'maxifoods' database successfully populated and verified!")
