import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

print("Adjusting time slots and order distributions to be 100% unique per restaurant type...")

df_orders = pd.read_csv(os.path.join(DATA_DIR, "fact_orders.csv"))
df_time = pd.read_csv(os.path.join(DATA_DIR, "dim_time.csv"))

# Map date to day_of_week
date_dow_map = dict(zip(df_time["date"], df_time["day_of_week"]))

# Time slot probabilities per restaurant category
# Order of slots: ["Morning", "Afternoon", "Evening", "Night"]
CATEGORY_SLOT_PROBS = {
    # South Veg Tiffin: High Morning, High Afternoon
    1: [0.38, 0.35, 0.18, 0.09],
    9: [0.42, 0.34, 0.16, 0.08],
    14: [0.40, 0.36, 0.16, 0.08],
    
    # Biryani & Mughlai: Low Morning, Very High Afternoon & Night
    7: [0.05, 0.48, 0.17, 0.30],
    12: [0.06, 0.46, 0.18, 0.30],
    3: [0.08, 0.36, 0.22, 0.34],
    11: [0.07, 0.35, 0.23, 0.35],
    
    # Bakery & Desserts: Low Morning, Low Afternoon, Very High Evening & Night
    6: [0.05, 0.15, 0.52, 0.28],
    13: [0.06, 0.18, 0.48, 0.28],
    
    # Juices & Sandwiches: Low Morning, High Afternoon, Very High Evening
    5: [0.10, 0.28, 0.48, 0.14],
    2: [0.12, 0.32, 0.42, 0.14],
    
    # Executive Combos / Chinese: Low Morning, Very High Afternoon, High Evening
    4: [0.08, 0.54, 0.26, 0.12],
    8: [0.12, 0.42, 0.32, 0.14],
    10: [0.15, 0.45, 0.28, 0.12],
    15: [0.14, 0.46, 0.26, 0.14]
}

np.random.seed(42)

new_slots = []
for idx, row in df_orders.iterrows():
    rid = int(row["restaurant_id"])
    probs = CATEGORY_SLOT_PROBS.get(rid, [0.20, 0.35, 0.30, 0.15])
    slot = np.random.choice(["Morning", "Afternoon", "Evening", "Night"], p=probs)
    new_slots.append(slot)

df_orders["order_time_slot"] = new_slots
df_orders.to_csv(os.path.join(DATA_DIR, "fact_orders.csv"), index=False)
print("Updated fact_orders.csv with unique time slot distributions!")

print("\nUpdating PostgreSQL fact_orders table...")
engine = create_engine("postgresql://postgres:postgres@localhost:5432/maxifoods")
df_order_items = pd.read_csv(os.path.join(DATA_DIR, "fact_order_items.csv"))

with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE fact_orders CASCADE;"))
    conn.commit()
    df_orders.to_sql("fact_orders", engine, if_exists="append", index=False)
    df_order_items.to_sql("fact_order_items", engine, if_exists="append", index=False)
    conn.commit()

print("PostgreSQL database successfully updated with unique restaurant time slots and items!")
