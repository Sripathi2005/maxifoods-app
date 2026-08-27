"""
Food Delivery Customer Intelligence - Analysis Pipeline
=========================================================
Runs on the star-schema CSVs produced by generate_dataset.py:
  1. Market Basket Analysis (Apriori -> association rules)
  2. RFM Segmentation + KMeans clustering
  3. Seasonal veg/non-veg trend analysis
  4. Monthly / weekday popular item analysis
  5. Discount impact analysis

Outputs CSVs to /home/claude/foodx/analysis/ and a single summarized
JSON for the dashboard.
"""

import os
import pandas as pd
import numpy as np
import json
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE_DIR, "data")
OUT = os.path.join(BASE_DIR, "analysis")
os.makedirs(OUT, exist_ok=True)

dim_customer = pd.read_csv(os.path.join(DATA, "dim_customer.csv"))
dim_restaurant = pd.read_csv(os.path.join(DATA, "dim_restaurant.csv"))
dim_food_item = pd.read_csv(os.path.join(DATA, "dim_food_item.csv"))
fact_orders = pd.read_csv(os.path.join(DATA, "fact_orders.csv"), parse_dates=["order_date"])
fact_order_items = pd.read_csv(os.path.join(DATA, "fact_order_items.csv"))

item_lookup = dim_food_item.set_index("item_id")

# ========================================================================
# 1. MARKET BASKET ANALYSIS (Apriori)
# ========================================================================
basket = fact_order_items.merge(dim_food_item[["item_id", "item_name"]], on="item_id")
top_item_names = basket["item_name"].value_counts().head(300).index
basket_filtered = basket[basket["item_name"].isin(top_item_names)]
basket_matrix = (basket_filtered.groupby(["order_id", "item_name"])["quantity"]
                  .sum().unstack().fillna(0))
basket_bool = (basket_matrix > 0)

frequent_itemsets = apriori(basket_bool, min_support=0.0001, max_len=2, use_colnames=True)
if not frequent_itemsets.empty:
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.05)
    rules = rules[rules["confidence"] >= 0.05].sort_values("lift", ascending=False)
else:
    rules = pd.DataFrame(columns=["antecedents", "consequents", "support", "confidence", "lift"])

rules_out = rules.copy()
if not rules_out.empty:
    rules_out["antecedents"] = rules_out["antecedents"].apply(lambda x: ", ".join(sorted(x)))
    rules_out["consequents"] = rules_out["consequents"].apply(lambda x: ", ".join(sorted(x)))
    rules_out = rules_out[["antecedents", "consequents", "support", "confidence", "lift"]]
    rules_out = rules_out.round(3).head(40)
rules_out.to_csv(os.path.join(OUT, "market_basket_rules.csv"), index=False)

# ========================================================================
# 2. RFM SEGMENTATION + KMEANS
# ========================================================================
snapshot_date = fact_orders["order_date"].max() + pd.Timedelta(days=1)
rfm = fact_orders.groupby("customer_id").agg(
    recency=("order_date", lambda x: (snapshot_date - x.max()).days),
    frequency=("order_id", "count"),
    monetary=("final_amount", "sum"),
).reset_index()

scaler = StandardScaler()
rfm_scaled = scaler.fit_transform(rfm[["recency", "frequency", "monetary"]])
km = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["cluster"] = km.fit_predict(rfm_scaled)

# Label clusters by their characteristics, ranked against each other
# (using cluster-mean rank order rather than absolute quantiles, since with
# only 4 clusters, quantile thresholds over 4 points are unstable)
cluster_profile = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean()
cluster_profile["value_score"] = cluster_profile["frequency"].rank() + cluster_profile["monetary"].rank() - cluster_profile["recency"].rank()
ordered = cluster_profile.sort_values("value_score", ascending=False).index.tolist()

label_pool = ["Loyal High-Spenders", "Steady Regulars", "New / Occasional", "At Risk / Churning"]
cluster_labels = {cluster_id: label_pool[i] for i, cluster_id in enumerate(ordered)}
rfm["segment"] = rfm["cluster"].map(cluster_labels)
rfm = rfm.merge(dim_customer[["customer_id", "customer_name", "diet_profile", "city"]], on="customer_id")
rfm.round(2).to_csv(f"{OUT}/rfm_segments.csv", index=False)

segment_summary = rfm.groupby("segment").agg(
    customers=("customer_id", "count"),
    avg_recency=("recency", "mean"),
    avg_frequency=("frequency", "mean"),
    avg_monetary=("monetary", "mean"),
).round(1).reset_index()
segment_summary.to_csv(f"{OUT}/segment_summary.csv", index=False)

# ========================================================================
# 3. SEASONAL VEG/NON-VEG TREND
# ========================================================================
fact_orders["month_year"] = fact_orders["order_date"].dt.to_period("M").astype(str)
monthly_veg = fact_orders.groupby("month_year").agg(
    total_orders=("order_id", "count"),
    veg_orders=("is_veg_order", "sum"),
).reset_index()
monthly_veg["veg_pct"] = (monthly_veg["veg_orders"] / monthly_veg["total_orders"] * 100).round(1)
monthly_veg.to_csv(f"{OUT}/monthly_veg_trend.csv", index=False)

season_veg = fact_orders.groupby("veg_season_tag").agg(
    total_orders=("order_id", "count"),
    veg_orders=("is_veg_order", "sum"),
).reset_index()
season_veg["veg_pct"] = (season_veg["veg_orders"] / season_veg["total_orders"] * 100).round(1)
season_veg.to_csv(f"{OUT}/season_veg_trend.csv", index=False)

# diet_profile x season breakdown (the core "flexitarian switch" proof)
orders_with_diet = fact_orders.merge(dim_customer[["customer_id", "diet_profile"]], on="customer_id")
orders_with_diet["season_bucket"] = np.where(orders_with_diet["veg_season_tag"] == "Regular", "Regular", "Veg Season")
diet_season = orders_with_diet.groupby(["diet_profile", "season_bucket"]).agg(
    total_orders=("order_id", "count"),
    veg_orders=("is_veg_order", "sum"),
).reset_index()
diet_season["veg_pct"] = (diet_season["veg_orders"] / diet_season["total_orders"] * 100).round(1)
diet_season.to_csv(f"{OUT}/diet_profile_season_trend.csv", index=False)

# ========================================================================
# 4. TOP ITEMS BY MONTH + BY WEEKDAY (what to crave, what's popular when)
# ========================================================================
oi_full = fact_order_items.merge(fact_orders[["order_id", "order_date", "veg_season_tag"]], on="order_id")
oi_full = oi_full.merge(dim_food_item[["item_id", "item_name", "veg_flag", "category"]], on="item_id")
oi_full["month_name"] = oi_full["order_date"].dt.month_name()
oi_full["weekday"] = oi_full["order_date"].dt.day_name()

top_items_month = (oi_full.groupby(["month_name", "item_name"])["quantity"].sum()
                    .reset_index().sort_values(["month_name", "quantity"], ascending=[True, False]))
top_items_month = top_items_month.groupby("month_name").head(5)
top_items_month.to_csv(f"{OUT}/top_items_by_month.csv", index=False)

# top VEG substitute items specifically during veg season (answers "what do they crave")
veg_season_items = oi_full[(oi_full["veg_season_tag"] != "Regular") & (oi_full["veg_flag"] == "Veg")]
top_veg_season_items = (veg_season_items.groupby("item_name")["quantity"].sum()
                         .reset_index().sort_values("quantity", ascending=False).head(10))
top_veg_season_items.to_csv(f"{OUT}/top_veg_season_items.csv", index=False)

top_items_weekday = (oi_full.groupby(["weekday", "item_name"])["quantity"].sum()
                      .reset_index().sort_values(["weekday", "quantity"], ascending=[True, False]))
top_items_weekday = top_items_weekday.groupby("weekday").head(3)
top_items_weekday.to_csv(f"{OUT}/top_items_by_weekday.csv", index=False)

# ========================================================================
# 5. DISCOUNT IMPACT
# ========================================================================
fact_orders["has_discount"] = fact_orders["discount_pct"] > 0
discount_impact = fact_orders.groupby("has_discount").agg(
    orders=("order_id", "count"),
    avg_order_value=("final_amount", "mean"),
    avg_items=("item_count", "mean"),
).round(2).reset_index()
discount_impact.to_csv(f"{OUT}/discount_impact.csv", index=False)

# ========================================================================
# 6. KPI SUMMARY + DASHBOARD JSON BUNDLE
# ========================================================================
kpis = {
    "total_orders": int(len(fact_orders)),
    "total_customers": int(dim_customer.shape[0]),
    "total_restaurants": int(dim_restaurant.shape[0]),
    "total_revenue": round(float(fact_orders["final_amount"].sum()), 2),
    "avg_order_value": round(float(fact_orders["final_amount"].mean()), 2),
    "overall_veg_pct": round(float(fact_orders["is_veg_order"].mean() * 100), 1),
    "avg_delivery_time": round(float(fact_orders["delivery_time_min"].mean()), 1),
    "avg_rating": round(float(fact_orders["rating_given"].mean()), 2),
}

top_overall_items = (fact_order_items.merge(dim_food_item[["item_id", "item_name"]], on="item_id")
                      .groupby("item_name")["quantity"].sum()
                      .reset_index().sort_values("quantity", ascending=False).head(10))

cuisine_perf = (fact_orders.merge(dim_restaurant[["restaurant_id", "primary_cuisine"]], on="restaurant_id")
                .groupby("primary_cuisine")["final_amount"].sum()
                .reset_index().sort_values("final_amount", ascending=False))

city_perf = (fact_orders.merge(dim_customer[["customer_id", "city"]], on="customer_id")
             .groupby("city")["final_amount"].sum()
             .reset_index().sort_values("final_amount", ascending=False))

time_slot_perf = fact_orders.groupby("order_time_slot")["order_id"].count().reset_index()
time_slot_perf.columns = ["time_slot", "orders"]

dashboard_bundle = {
    "kpis": kpis,
    "monthly_veg_trend": monthly_veg.to_dict(orient="records"),
    "season_veg_trend": season_veg.to_dict(orient="records"),
    "diet_profile_season_trend": diet_season.to_dict(orient="records"),
    "top_overall_items": top_overall_items.to_dict(orient="records"),
    "top_items_by_month": top_items_month.to_dict(orient="records"),
    "top_veg_season_items": top_veg_season_items.to_dict(orient="records"),
    "top_items_by_weekday": top_items_weekday.to_dict(orient="records"),
    "cuisine_perf": cuisine_perf.to_dict(orient="records"),
    "city_perf": city_perf.to_dict(orient="records"),
    "time_slot_perf": time_slot_perf.to_dict(orient="records"),
    "segment_summary": segment_summary.to_dict(orient="records"),
    "discount_impact": discount_impact.to_dict(orient="records"),
    "market_basket_rules": rules_out.to_dict(orient="records"),
}

with open(f"{OUT}/dashboard_data.json", "w") as f:
    json.dump(dashboard_bundle, f, indent=2, default=str)

print("KPIs:", kpis)
print(f"\nAssociation rules found: {len(rules_out)}")
print(rules_out.head(8).to_string(index=False))
print(f"\nSegments:\n{segment_summary}")
