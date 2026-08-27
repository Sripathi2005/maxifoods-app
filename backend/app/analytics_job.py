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
        logger.info("Starting memory-optimized analytics pipeline...")

        # ----------------------------------------------------------------------
        # 1. MARKET BASKET ANALYSIS (Apriori - Memory Guarded)
        # ----------------------------------------------------------------------
        rule_count = db.query(AnalyticsMarketBasketRule).count()
        if rule_count == 0:
            import os
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "analysis", "market_basket_rules.csv")
            if os.path.exists(csv_path):
                rules_df = pd.read_csv(csv_path)
                for _, row in rules_df.head(50).iterrows():
                    db.add(AnalyticsMarketBasketRule(
                        antecedents=str(row["antecedents"]),
                        consequents=str(row["consequents"]),
                        support=round(float(row["support"]), 4),
                        confidence=round(float(row["confidence"]), 4),
                        lift=round(float(row["lift"]), 4),
                        updated_at=datetime.utcnow()
                    ))
                db.commit()
                logger.info("Seeded market basket rules from pre-computed analysis CSV.")
        else:
            # Memory-guarded sample calculation (limit to 2500 records to prevent OOM)
            items_query = db.query(
                FactOrderItem.order_id,
                DimFoodItem.item_name,
                FactOrderItem.quantity
            ).join(DimFoodItem, FactOrderItem.item_id == DimFoodItem.item_id).limit(2500).all()

            if items_query:
                basket_df = pd.DataFrame(items_query, columns=["order_id", "item_name", "quantity"])
                basket_matrix = (basket_df.groupby(["order_id", "item_name"])["quantity"]
                                 .sum().unstack().fillna(0))
                basket_bool = (basket_matrix > 0)

                frequent_itemsets = apriori(basket_bool, min_support=0.01, use_colnames=True)
                if not frequent_itemsets.empty:
                    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
                    if not rules.empty:
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
                        db.query(AnalyticsMarketBasketRule).delete()
                        for r in rules_clean:
                            db.add(AnalyticsMarketBasketRule(**r))
                        db.commit()

        # ----------------------------------------------------------------------
        # 2. RFM SEGMENTATION + K-MEANS CLUSTERING (Memory Guarded)
        # ----------------------------------------------------------------------
        segment_count = db.query(AnalyticsRFMSegment).count()
        if segment_count == 0:
            import os
            rfm_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "analysis", "rfm_segments.csv")
            if os.path.exists(rfm_csv_path):
                rfm_df = pd.read_csv(rfm_csv_path)
                for _, row in rfm_df.head(2000).iterrows():
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
                logger.info("Seeded RFM segments from pre-computed analysis CSV.")

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
