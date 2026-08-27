import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import (
    DimCustomer, DimRestaurant, DimFoodItem, DimTime,
    FactOrder, FactOrderItem, User, UserRole
)
from backend.app.auth import get_password_hash
from backend.app.analytics_job import run_analytics_pipeline

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def ensure_database_exists():
    """Ensure PostgreSQL target database exists."""
    root_engine = create_engine(settings.ROOT_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with root_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{settings.POSTGRES_DB}'"))
        if not result.fetchone():
            print(f"Database '{settings.POSTGRES_DB}' does not exist. Creating...")
            conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DB}"))
            print(f"Database '{settings.POSTGRES_DB}' created successfully.")
        else:
            print(f"Database '{settings.POSTGRES_DB}' already exists.")

def seed_star_schema(db_engine):
    """Seed CSV data into PostgreSQL star schema tables."""
    print("Creating tables in PostgreSQL...")
    Base.metadata.create_all(bind=db_engine)

    with SessionLocal() as db:
        if db.query(FactOrder).count() > 0:
            print("Star schema data already present in database. Skipping CSV seed.")
            return

    print("Loading CSV files into pandas dataframes...")

    # Load CSVs
    dim_customer_df = pd.read_csv(os.path.join(DATA_DIR, "dim_customer.csv"))
    dim_restaurant_df = pd.read_csv(os.path.join(DATA_DIR, "dim_restaurant.csv"))
    dim_food_item_df = pd.read_csv(os.path.join(DATA_DIR, "dim_food_item.csv"))
    dim_time_df = pd.read_csv(os.path.join(DATA_DIR, "dim_time.csv"))
    fact_orders_df = pd.read_csv(os.path.join(DATA_DIR, "fact_orders.csv"))
    fact_order_items_df = pd.read_csv(os.path.join(DATA_DIR, "fact_order_items.csv"))

    # Type conversions
    dim_customer_df["signup_date"] = pd.to_datetime(dim_customer_df["signup_date"]).dt.date
    dim_time_df["date"] = pd.to_datetime(dim_time_df["date"]).dt.date
    dim_time_df["is_weekend"] = dim_time_df["is_weekend"].astype(bool)
    
    fact_orders_df["order_date"] = pd.to_datetime(fact_orders_df["order_date"]).dt.date
    fact_orders_df["is_veg_order"] = fact_orders_df["is_veg_order"].astype(int)

    print("Inserting data into PostgreSQL tables (this may take a few seconds)...")
    dim_customer_df.to_sql("dim_customer", db_engine, if_exists="append", index=False)
    print(" -> dim_customer loaded.")
    
    dim_restaurant_df.to_sql("dim_restaurant", db_engine, if_exists="append", index=False)
    print(" -> dim_restaurant loaded.")

    dim_food_item_df.to_sql("dim_food_item", db_engine, if_exists="append", index=False)
    print(" -> dim_food_item loaded.")

    dim_time_df.to_sql("dim_time", db_engine, if_exists="append", index=False)
    print(" -> dim_time loaded.")

    fact_orders_df.to_sql("fact_orders", db_engine, if_exists="append", index=False, chunksize=5000)
    print(" -> fact_orders loaded.")

    fact_order_items_df.to_sql("fact_order_items", db_engine, if_exists="append", index=False, chunksize=10000)
    print(" -> fact_order_items loaded.")

def seed_users():
    """Create sample customer and 10 restaurant owner accounts."""
    db = SessionLocal()
    try:
        default_pwd = get_password_hash("password123")

        # 1. Customer User
        if not db.query(User).filter(User.email == "customer@maxifoods.com").first():
            customer_user = User(
                name="Demo Customer",
                email="customer@maxifoods.com",
                password_hash=default_pwd,
                role=UserRole.CUSTOMER.value,
                restaurant_id=None
            )
            db.add(customer_user)
            print(" -> Created customer account: customer@maxifoods.com")

        # 2. 10 Sample Restaurant Owners
        top_restaurants = (
            db.query(DimRestaurant)
            .join(FactOrder, DimRestaurant.restaurant_id == FactOrder.restaurant_id)
            .group_by(DimRestaurant.restaurant_id)
            .order_by(text("count(fact_orders.order_id) DESC"))
            .limit(10)
            .all()
        )

        for i, rest in enumerate(top_restaurants, start=1):
            email = f"owner{i}@maxifoods.com"
            if not db.query(User).filter(User.email == email).first():
                owner_user = User(
                    name=f"Owner ({rest.restaurant_name})",
                    email=email,
                    password_hash=default_pwd,
                    role=UserRole.RESTAURANT_OWNER.value,
                    restaurant_id=rest.restaurant_id
                )
                db.add(owner_user)
                print(f" -> Created owner account #{i}: {email} (Linked to: {rest.restaurant_name}, ID={rest.restaurant_id})")

        db.commit()
    finally:
        db.close()

def main():
    print("=== MaxiFoods Database Seeding ===")
    ensure_database_exists()
    seed_star_schema(engine)
    seed_users()
    print("Running initial analytics pipeline recomputation...")
    run_analytics_pipeline()
    print("=== Database Seeding Complete! ===")

if __name__ == "__main__":
    main()
