"""
Food Delivery Customer Intelligence - Synthetic Dataset Generator
====================================================================
Generates a star-schema dataset (Dim_Customer, Dim_Restaurant, Dim_FoodItem,
Fact_Orders, Fact_Order_Items) for a food delivery platform, with a
deliberately injected behavioral pattern:

  - Some customers ("flexitarians") switch from non-veg to veg ordering
    during real Indian fasting/festival windows (Shravan, Navratri).
  - Discounts are more frequent during festival windows.
  - Items are paired using realistic combo logic (curry+bread, biryani+raita,
    chinese main+fried rice) so Market Basket Analysis has real patterns
    to discover, not random noise.

Output: CSVs in /home/claude/foodx/data/ following a star schema.
"""

import os
import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE_DIR, "data")
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------
# 1. DIM_TIME - date range with festival/fasting windows tagged
# ----------------------------------------------------------------------
START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)

# Real Indian veg-heavy / fasting windows (approx, for demo purposes)
VEG_WINDOWS = [
    ("2024-04-09", "2024-04-17", "Chaitra Navratri"),
    ("2024-08-05", "2024-09-03", "Shravan"),
    ("2024-10-03", "2024-10-12", "Sharad Navratri"),
    ("2025-03-30", "2025-04-07", "Chaitra Navratri"),
    ("2025-07-25", "2025-08-23", "Shravan"),
    ("2025-09-22", "2025-10-01", "Sharad Navratri"),
]
VEG_WINDOWS = [(pd.Timestamp(s), pd.Timestamp(e), name) for s, e, name in VEG_WINDOWS]

def tag_veg_season(d):
    ts = pd.Timestamp(d)
    for s, e, name in VEG_WINDOWS:
        if s <= ts <= e:
            return name
    return "Regular"

dates = pd.date_range(START_DATE, END_DATE, freq="D")
dim_time = pd.DataFrame({"date": dates})
dim_time["day_of_week"] = dim_time["date"].dt.day_name()
dim_time["is_weekend"] = dim_time["date"].dt.dayofweek >= 5
dim_time["month"] = dim_time["date"].dt.month
dim_time["month_name"] = dim_time["date"].dt.month_name()
dim_time["year"] = dim_time["date"].dt.year
dim_time["veg_season_tag"] = dim_time["date"].apply(tag_veg_season)
dim_time.to_csv(os.path.join(OUT, "dim_time.csv"), index=False)

# ----------------------------------------------------------------------
# 2. DIM_RESTAURANT
# ----------------------------------------------------------------------
CITIES = ["Chennai", "Bangalore", "Hyderabad", "Mumbai", "Pune", "Delhi"]
CUISINES = ["North Indian", "South Indian", "Chinese", "Biryani Specialist",
            "Multi-Cuisine", "Desserts & Bakery"]

restaurant_names = [
    "Spice Route", "Tandoori Nights", "Coastal Curry House", "Biryani Junction",
    "Dragon Wok", "Saravana Bhavan Express", "The Curry Leaf", "Punjabi Tadka",
    "Chettinad Corner", "Momo Street", "Andhra Mess", "Royal Biryani House",
    "Green Bowl Kitchen", "Wok This Way", "Sweet Ending Desserts",
    "Grill & Chill", "Masala Box", "Idli Dosa Point", "Kebab Junction",
    "Paradise Biryani", "Hakka Noodle Co.", "Ghee Roast Diner", "Naan Stop",
    "Curry Culture", "Rice Bowl Republic", "The Veg Table", "Spice Symphony",
    "Chicken & Chai", "South Blend Cafe", "Urban Tandoor",
]

n_rest = len(restaurant_names)
dim_restaurant = pd.DataFrame({
    "restaurant_id": range(1, n_rest + 1),
    "restaurant_name": restaurant_names,
    "city": np.random.choice(CITIES, n_rest),
    "primary_cuisine": np.random.choice(CUISINES, n_rest),
    "avg_rating": np.round(np.random.uniform(3.4, 4.8, n_rest), 1),
    "total_ratings": np.random.randint(150, 9000, n_rest),
    "cost_for_two": np.random.choice([250, 350, 450, 600, 800], n_rest),
})

OFFER_TEMPLATES = [
    "FLAT 20% OFF up to Rs.100",
    "50% OFF up to Rs.80 on orders above Rs.199",
    "FLAT Rs.75 OFF above Rs.399",
    "Free delivery on orders above Rs.149",
    "Buy 1 Get 1 on select Starters",
    "FLAT 15% OFF up to Rs.60",
    "30% OFF up to Rs.120 for new users",
]
dim_restaurant["current_offer"] = [
    random.choice(OFFER_TEMPLATES) if random.random() < 0.75 else "No active offer"
    for _ in range(n_rest)
]
dim_restaurant.to_csv(os.path.join(OUT, "dim_restaurant.csv"), index=False)

# ----------------------------------------------------------------------
# 3. DIM_FOOD_ITEM - authentic real-world Indian food pairings
# ----------------------------------------------------------------------
menu = [
    # (item_name, category, veg_flag, price, combo_group, substitute_group)
    ("Chicken Biryani", "Biryani", "Non-Veg", 240, "biryani_main", "biryani"),
    ("Mutton Biryani", "Biryani", "Non-Veg", 300, "biryani_main", "biryani"),
    ("Egg Biryani", "Biryani", "Egg", 180, "biryani_main", "biryani"),
    ("Veg Biryani", "Biryani", "Veg", 190, "biryani_main", "biryani"),
    ("Paneer Biryani", "Biryani", "Veg", 210, "biryani_main", "biryani"),

    ("Butter Chicken", "Curry", "Non-Veg", 260, "curry_main", "curry"),
    ("Chicken Curry", "Curry", "Non-Veg", 230, "curry_main", "curry"),
    ("Fish Curry", "Curry", "Non-Veg", 270, "curry_main", "curry"),
    ("Paneer Butter Masala", "Curry", "Veg", 220, "curry_main", "curry"),
    ("Dal Makhani", "Curry", "Veg", 180, "curry_main", "curry"),
    ("Chana Masala", "Curry", "Veg", 170, "curry_main", "curry"),
    ("Mushroom Masala", "Curry", "Veg", 190, "curry_main", "curry"),

    ("Chicken 65", "Starter", "Non-Veg", 210, "biryani_starter", "starter"),
    ("Fish Fry", "Starter", "Non-Veg", 240, "starter", "starter"),
    ("Chicken Tikka", "Starter", "Non-Veg", 230, "curry_starter", "starter"),
    ("Gobi Manchurian", "Starter", "Veg", 180, "starter", "starter"),
    ("Paneer Tikka", "Starter", "Veg", 200, "curry_starter", "starter"),
    ("Veg Spring Rolls", "Starter", "Veg", 170, "chinese_starter", "starter"),

    ("Butter Naan", "Bread", "Veg", 55, "bread", None),
    ("Garlic Naan", "Bread", "Veg", 65, "bread", None),
    ("Tandoori Roti", "Bread", "Veg", 35, "bread", None),
    ("Rumali Roti", "Bread", "Veg", 40, "bread", None),

    ("Jeera Rice", "Rice", "Veg", 130, "rice", None),
    ("Egg Fried Rice", "Rice", "Egg", 160, "chinese_main", "rice"),
    ("Veg Fried Rice", "Rice", "Veg", 150, "chinese_main", "rice"),
    ("Chicken Fried Rice", "Rice", "Non-Veg", 190, "chinese_main", "rice"),

    ("Chicken Chettinad", "South Indian", "Non-Veg", 250, "south_main", "south"),
    ("Masala Dosa", "South Indian", "Veg", 120, "south_main", "south"),
    ("Idli Sambar", "South Indian", "Veg", 90, "south_main", "south"),
    ("Uttapam", "South Indian", "Veg", 110, "south_main", "south"),
    ("Chettinad Egg Curry", "South Indian", "Egg", 170, "south_main", "south"),
    ("Medu Vada", "South Indian", "Veg", 60, "south_side", "south"),

    ("Chicken Manchurian", "Chinese", "Non-Veg", 220, "chinese_main", "chinese"),
    ("Chicken Noodles", "Chinese", "Non-Veg", 190, "chinese_main", "chinese"),
    ("Veg Manchurian", "Chinese", "Veg", 180, "chinese_main", "chinese"),
    ("Veg Noodles", "Chinese", "Veg", 160, "chinese_main", "chinese"),
    ("Veg Fried Momos", "Chinese", "Veg", 140, "chinese_starter", "chinese"),
    ("Chicken Momos", "Chinese", "Non-Veg", 170, "chinese_starter", "chinese"),

    ("Gulab Jamun", "Dessert", "Veg", 70, "dessert", None),
    ("Rasmalai", "Dessert", "Veg", 90, "dessert", None),
    ("Ice Cream", "Dessert", "Veg", 80, "dessert", None),

    ("Sweet Lassi", "Beverage", "Veg", 60, "curry_beverage", None),
    ("Buttermilk", "Beverage", "Veg", 40, "south_beverage", None),
    ("Soft Drink", "Beverage", "Veg", 50, "biryani_beverage", None),
    ("Filter Coffee", "Beverage", "Veg", 45, "south_beverage", None),

    ("Raita", "Sides", "Veg", 45, "biryani_side", None),
    ("Mirchi Ka Salan", "Sides", "Veg", 50, "biryani_side", None),
    ("Papad", "Sides", "Veg", 25, "curry_side", None),
]

dim_food_item = pd.DataFrame(menu, columns=[
    "item_name", "category", "veg_flag", "price", "combo_group", "substitute_group"
])
dim_food_item.insert(0, "item_id", range(1, len(dim_food_item) + 1))
dim_food_item.to_csv(os.path.join(OUT, "dim_food_item.csv"), index=False)

CATEGORY_CUISINE = {
    "Biryani":       ["Biryani Specialist", "Multi-Cuisine"],
    "Curry":         ["North Indian", "Multi-Cuisine"],
    "Starter":       ["North Indian", "Chinese", "Multi-Cuisine"],
    "South Indian":  ["South Indian", "Multi-Cuisine"],
    "Chinese":       ["Chinese", "Multi-Cuisine"],
}

def eligible_restaurants(category):
    cuisines = CATEGORY_CUISINE.get(category, None)
    if not cuisines:
        return dim_restaurant
    pool = dim_restaurant[dim_restaurant["primary_cuisine"].isin(cuisines)]
    return pool if len(pool) > 0 else dim_restaurant

items_by_group = dim_food_item.groupby("combo_group")["item_id"].apply(list).to_dict()
mains = dim_food_item[dim_food_item["combo_group"].str.contains("main", na=False)]
mains_veg = mains[mains["veg_flag"] == "Veg"]
mains_nonveg = mains[mains["veg_flag"].isin(["Non-Veg", "Egg"])]
item_lookup = dim_food_item.set_index("item_id")

# AUTHENTIC CULINARY PAIRINGS:
# Biryani -> Raita / Mirchi Ka Salan + Chicken 65 + Soft Drink / Gulab Jamun
# Curry -> Butter Naan / Tandoori Roti + Jeera Rice + Papad + Sweet Lassi
# South Indian -> Medu Vada + Filter Coffee / Buttermilk
# Chinese -> Fried Rice/Noodles + Veg Spring Rolls / Momos + Soft Drink
PAIRING = {
    "biryani_main": ["biryani_side", "biryani_starter", "biryani_beverage", "dessert"],
    "curry_main": ["bread", "rice", "curry_side", "curry_beverage"],
    "starter": ["curry_beverage"],
    "south_main": ["south_side", "south_beverage"],
    "chinese_main": ["chinese_starter", "biryani_beverage"],
}


# ----------------------------------------------------------------------
# 4. DIM_CUSTOMER - with a diet_profile driving seasonal behavior
#    - mostly_nonveg: rarely orders veg, doesn't shift much
#    - mostly_veg: always orders veg
#    - flexitarian: normally non-veg, but STRONGLY shifts to veg during
#      veg_season windows -> this is the pattern the whole project is
#      built to discover
# ----------------------------------------------------------------------
N_CUSTOMERS = 450
first_names = ["Aarav","Vihaan","Aditya","Sai","Reyansh","Ishaan","Kabir","Arjun",
    "Ananya","Diya","Saanvi","Myra","Aadhya","Kiara","Pari","Anika","Riya","Meera",
    "Rohan","Karthik","Priya","Divya","Sneha","Vikram","Arun","Lakshmi","Deepa",
    "Manoj","Ramesh","Suresh","Kavya","Nisha","Rahul","Varun","Pooja","Anjali"]
last_names = ["Sharma","Reddy","Iyer","Nair","Menon","Rao","Gupta","Verma","Pillai",
    "Krishnan","Subramanian","Patel","Naidu","Chandran","Raman","Mehta","Joshi"]

diet_profiles = np.random.choice(
    ["mostly_nonveg", "mostly_veg", "flexitarian"],
    N_CUSTOMERS, p=[0.45, 0.25, 0.30]
)

dim_customer = pd.DataFrame({
    "customer_id": range(1, N_CUSTOMERS + 1),
    "customer_name": [f"{random.choice(first_names)} {random.choice(last_names)}" for _ in range(N_CUSTOMERS)],
    "age": np.random.randint(18, 45, N_CUSTOMERS),
    "gender": np.random.choice(["Male", "Female"], N_CUSTOMERS, p=[0.56, 0.44]),
    "city": np.random.choice(CITIES, N_CUSTOMERS),
    "diet_profile": diet_profiles,
    "signup_date": [START_DATE + timedelta(days=int(np.random.randint(0, 300))) for _ in range(N_CUSTOMERS)],
})
dim_customer.to_csv(os.path.join(OUT, "dim_customer.csv"), index=False)

# ----------------------------------------------------------------------
# 5. FACT_ORDERS + FACT_ORDER_ITEMS
#    Each customer places orders at some average weekly rate.
#    Veg-ordering probability depends on diet_profile x veg_season_tag.
# ----------------------------------------------------------------------
VEG_PROB = {
    "mostly_nonveg":   {"Regular": 0.15, "veg_season": 0.35},
    "mostly_veg":      {"Regular": 0.92, "veg_season": 0.97},
    "flexitarian":     {"Regular": 0.30, "veg_season": 0.88},  # the big swing
}

orders_rows = []
order_items_rows = []
order_id_ctr = 1
oi_id_ctr = 1

time_slots = ["Morning", "Afternoon", "Evening", "Night"]
time_slot_weights = [0.10, 0.20, 0.45, 0.25]

for _, cust in dim_customer.iterrows():
    cust_id = cust["customer_id"]
    diet = cust["diet_profile"]
    weekly_rate = np.random.uniform(0.6, 2.2)
    signup = pd.Timestamp(cust["signup_date"])
    active_days = pd.date_range(max(signup, pd.Timestamp(START_DATE)), END_DATE, freq="D")
    n_orders = int(len(active_days) / 7 * weekly_rate)
    if n_orders < 1:
        continue
    order_dates = np.random.choice(active_days, size=n_orders, replace=True)
    order_dates = sorted(pd.to_datetime(order_dates))

    for od in order_dates:
        season_tag = tag_veg_season(od)
        season_key = "veg_season" if season_tag != "Regular" else "Regular"
        p_veg = VEG_PROB[diet][season_key]

        want_veg = np.random.random() < p_veg
        main_group = np.random.choice(["biryani_main", "curry_main", "starter", "south_main", "chinese_main"],
                                       p=[0.28, 0.27, 0.13, 0.14, 0.18])
        pool = mains_veg if want_veg else mains_nonveg
        pool = pool[pool["combo_group"] == main_group]
        if pool.empty:
            pool = mains_veg[mains_veg["combo_group"] == main_group] if want_veg else mains
        if pool.empty:
            continue
        main_item = pool.sample(1).iloc[0]

        restaurant = eligible_restaurants(main_item["category"]).sample(1).iloc[0]
        discount_base = 0.12
        if season_tag != "Regular":
            discount_base = 0.30  # platforms push festival promos
        has_discount = np.random.random() < discount_base
        discount_pct = int(np.random.choice([10, 15, 20, 25, 30])) if has_discount else 0

        order_id = order_id_ctr
        order_id_ctr += 1

        basket_items = [main_item["item_id"]]
        # add-ons based on pairing rules
        addon_groups = PAIRING.get(main_group, [])
        for g in addon_groups:
            if np.random.random() < 0.55:
                cands = items_by_group.get(g, [])
                if cands:
                    basket_items.append(int(np.random.choice(cands)))
        # occasional dessert
        if np.random.random() < 0.18:
            basket_items.extend(items_by_group.get("dessert", [])[:1])
        # dedupe
        basket_items = list(dict.fromkeys(basket_items))

        total_amount = 0
        for it_id in basket_items:
            qty = 1 if np.random.random() < 0.85 else 2
            price = float(item_lookup.loc[it_id, "price"])
            line_total = price * qty
            total_amount += line_total
            order_items_rows.append({
                "order_item_id": oi_id_ctr,
                "order_id": order_id,
                "item_id": it_id,
                "quantity": qty,
                "unit_price": price,
                "line_total": round(line_total, 2),
            })
            oi_id_ctr += 1

        discount_amount = round(total_amount * discount_pct / 100, 2)
        delivery_fee = float(np.random.choice([0, 20, 30, 40], p=[0.25, 0.35, 0.25, 0.15]))
        final_amount = round(total_amount - discount_amount + delivery_fee, 2)
        delivery_time_min = int(np.random.normal(38, 10))
        delivery_time_min = max(15, min(90, delivery_time_min))
        rating_given = int(np.clip(np.random.normal(4.2, 0.7), 1, 5).round())

        orders_rows.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "restaurant_id": restaurant["restaurant_id"],
            "order_date": od.date().isoformat(),
            "order_time_slot": np.random.choice(time_slots, p=time_slot_weights),
            "veg_season_tag": season_tag,
            "is_veg_order": all(item_lookup.loc[i, "veg_flag"] == "Veg" for i in basket_items),
            "item_count": len(basket_items),
            "gross_amount": round(total_amount, 2),
            "discount_pct": discount_pct,
            "discount_amount": discount_amount,
            "delivery_fee": delivery_fee,
            "final_amount": final_amount,
            "delivery_time_min": delivery_time_min,
            "rating_given": rating_given,
        })

fact_orders = pd.DataFrame(orders_rows)
fact_order_items = pd.DataFrame(order_items_rows)

fact_orders.to_csv(os.path.join(OUT, "fact_orders.csv"), index=False)
fact_order_items.to_csv(os.path.join(OUT, "fact_order_items.csv"), index=False)

print(f"Customers: {len(dim_customer)}")
print(f"Restaurants: {len(dim_restaurant)}")
print(f"Food items: {len(dim_food_item)}")
print(f"Orders: {len(fact_orders)}")
print(f"Order line items: {len(fact_order_items)}")
print(f"Veg orders during veg_season vs regular:")
print(fact_orders.groupby("veg_season_tag")["is_veg_order"].mean().round(2))
