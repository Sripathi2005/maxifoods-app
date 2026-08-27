import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

food_csv = os.path.join(DATA_DIR, "dim_food_item.csv")
df_food = pd.read_csv(food_csv)

print("Tagging Egg dishes in dim_food_item...")

def classify_veg_flag(row):
    name = str(row["item_name"]).lower()
    flag = str(row["veg_flag"])
    if "egg" in name or "omelette" in name or "omlet" in name or "muttai" in name:
        return "Egg"
    return flag

df_food["veg_flag"] = df_food.apply(classify_veg_flag, axis=1)
df_food.to_csv(food_csv, index=False)
print("Updated dim_food_item.csv with Egg flags!")
print("Veg flag distribution in catalog:")
print(df_food["veg_flag"].value_counts())

# Update PostgreSQL maxifoods database
print("\nUpdating PostgreSQL database...")
engine = create_engine("postgresql://postgres:postgres@localhost:5432/maxifoods")
with engine.connect() as conn:
    for idx, row in df_food.iterrows():
        if row["veg_flag"] == "Egg":
            conn.execute(
                text("UPDATE dim_food_item SET veg_flag = 'Egg' WHERE item_id = :item_id"),
                {"item_id": row["item_id"]}
            )
    conn.commit()

print("PostgreSQL dim_food_item successfully updated with Egg flags!")
