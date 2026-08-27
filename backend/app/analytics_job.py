import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from mlxtend.frequent_patterns import apriori, association_rules
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from apscheduler.schedulers.background import BackgroundScheduler
import logging

from backend.app.database import SessionLocal, engine
from backend.app.models import (
    FactOrder, FactOrderItem, DimFoodItem, DimCustomer,
    AnalyticsMarketBasketRule, AnalyticsRFMSegment
)

logger = logging.getLogger("maxifoods.analytics")

def run_analytics_pipeline(db: Session = None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        logger.info("Starting analytics pipeline recomputation...")

        # ----------------------------------------------------------------------
        # 1. MARKET BASKET ANALYSIS (Apriori)
        # ----------------------------------------------------------------------
        # Load order items and item names directly from DB
        items_query = db.query(
            FactOrderItem.order_id,
            DimFoodItem.item_name,
            FactOrderItem.quantity
        ).join(DimFoodItem, FactOrderItem.item_id == DimFoodItem.item_id).all()

        if items_query:
            basket_df = pd.DataFrame(items_query, columns=["order_id", "item_name", "quantity"])
            basket_matrix = (basket_df.groupby(["order_id", "item_name"])["quantity"]
                             .sum().unstack().fillna(0))
            basket_bool = (basket_matrix > 0)

            frequent_itemsets = apriori(basket_bool, min_support=0.003, use_colnames=True)
            if not frequent_itemsets.empty:
                rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.1)
                rules = rules[rules["confidence"] >= 0.10].sort_values("lift", ascending=False)

                # Format antecedents & consequents
                rules_clean = []
                for _, row in rules.head(50).iterrows():
                    ante = ", ".join(sorted(list(row["antecedents"])))
                    cons = ", ".join(sorted(list(row["consequents"])))
                    rules_clean.append({
                        "antecedents": ante,
                        "consequents": cons,
                        "support": round(float(row["support"]), 4),
                        "confidence": round(float(row["confidence"]), 4),
                        "lift": round(float(row["lift"]), 4),
                        "updated_at": datetime.utcnow()
                    })

                # Truncate existing rules & insert new ones
                db.query(AnalyticsMarketBasketRule).delete()
                for r in rules_clean:
                    db.add(AnalyticsMarketBasketRule(**r))
                db.commit()
                logger.info(f"Updated {len(rules_clean)} market basket rules in PostgreSQL.")

        # ----------------------------------------------------------------------
        # 2. RFM SEGMENTATION + K-MEANS CLUSTERING
        # ----------------------------------------------------------------------
        orders_query = db.query(
            FactOrder.customer_id,
            FactOrder.order_id,
            FactOrder.order_date,
            FactOrder.final_amount
        ).all()

        if orders_query:
            orders_df = pd.DataFrame(orders_query, columns=["customer_id", "order_id", "order_date", "final_amount"])
            orders_df["order_date"] = pd.to_datetime(orders_df["order_date"])

            snapshot_date = orders_df["order_date"].max() + pd.Timedelta(days=1)
            rfm = orders_df.groupby("customer_id").agg(
                recency=("order_date", lambda x: (snapshot_date - x.max()).days),
                frequency=("order_id", "count"),
                monetary=("final_amount", "sum"),
            ).reset_index()

            if len(rfm) >= 4:
                scaler = StandardScaler()
                rfm_scaled = scaler.fit_transform(rfm[["recency", "frequency", "monetary"]])
                km = KMeans(n_clusters=4, random_state=42, n_init=10)
                rfm["cluster"] = km.fit_predict(rfm_scaled)

                cluster_profile = rfm.groupby("cluster")[["recency", "frequency", "monetary"]].mean()
                cluster_profile["value_score"] = (
                    cluster_profile["frequency"].rank() + 
                    cluster_profile["monetary"].rank() - 
                    cluster_profile["recency"].rank()
                )
                ordered = cluster_profile.sort_values("value_score", ascending=False).index.tolist()
                label_pool = ["Loyal High-Spenders", "Steady Regulars", "New / Occasional", "At Risk / Churning"]
                cluster_labels = {cluster_id: label_pool[i] for i, cluster_id in enumerate(ordered)}
                rfm["segment"] = rfm["cluster"].map(cluster_labels)

                # Clear & replace RFM segments table
                db.query(AnalyticsRFMSegment).delete()
                for _, row in rfm.iterrows():
                    db.add(AnalyticsRFMSegment(
                        customer_id=int(row["customer_id"]),
                        recency=int(row["recency"]),
                        frequency=int(row["frequency"]),
                        monetary=round(float(row["monetary"]), 2),
                        cluster=int(row["cluster"]),
                        segment=str(row["segment"]),
                        updated_at=datetime.utcnow()
                    ))
                db.commit()
                logger.info(f"Updated RFM segments for {len(rfm)} customers in PostgreSQL.")

    except Exception as e:
        logger.error(f"Error in analytics pipeline execution: {e}", exc_info=True)
        db.rollback()
    finally:
        if close_db:
            db.close()

# APScheduler setup
scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(run_analytics_pipeline, 'interval', hours=24, id='daily_analytics_recomputation')
    scheduler.start()
    logger.info("APScheduler initialized for daily analytics recomputation.")

def stop_scheduler():
    scheduler.shutdown(wait=False)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Running analytics pipeline manually...")
    run_analytics_pipeline()
    print("Done.")
