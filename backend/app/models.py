from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.app.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    RESTAURANT_OWNER = "restaurant_owner"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.CUSTOMER.value)
    restaurant_id = Column(Integer, ForeignKey("dim_restaurant.restaurant_id"), nullable=True)

    restaurant = relationship("DimRestaurant", back_populates="owners")

class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255))
    age = Column(Integer)
    gender = Column(String(50))
    city = Column(String(100))
    diet_profile = Column(String(100))
    signup_date = Column(Date)

    orders = relationship("FactOrder", back_populates="customer")

class DimRestaurant(Base):
    __tablename__ = "dim_restaurant"

    restaurant_id = Column(Integer, primary_key=True, index=True)
    restaurant_name = Column(String(255), nullable=False)
    city = Column(String(100))
    primary_cuisine = Column(String(100))
    avg_rating = Column(Float)
    total_ratings = Column(Integer)
    cost_for_two = Column(Integer)
    current_offer = Column(String(255))

    owners = relationship("User", back_populates="restaurant")
    orders = relationship("FactOrder", back_populates="restaurant")

class DimFoodItem(Base):
    __tablename__ = "dim_food_item"

    item_id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(255), nullable=False)
    category = Column(String(100))
    veg_flag = Column(String(50))
    price = Column(Float)
    combo_group = Column(String(100))
    substitute_group = Column(String(100))

    order_items = relationship("FactOrderItem", back_populates="food_item")

class DimTime(Base):
    __tablename__ = "dim_time"

    date = Column(Date, primary_key=True, index=True)
    day_of_week = Column(String(50))
    is_weekend = Column(Boolean)
    month = Column(Integer)
    month_name = Column(String(50))
    year = Column(Integer)
    veg_season_tag = Column(String(100))

    orders = relationship("FactOrder", back_populates="time_dim")

class FactOrder(Base):
    __tablename__ = "fact_orders"

    order_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("dim_customer.customer_id"), index=True)
    restaurant_id = Column(Integer, ForeignKey("dim_restaurant.restaurant_id"), index=True)
    order_date = Column(Date, ForeignKey("dim_time.date"), index=True)
    order_time_slot = Column(String(50))
    veg_season_tag = Column(String(100))
    is_veg_order = Column(Integer)
    item_count = Column(Integer)
    gross_amount = Column(Float)
    discount_pct = Column(Float)
    discount_amount = Column(Float)
    delivery_fee = Column(Float)
    final_amount = Column(Float)
    delivery_time_min = Column(Float)
    rating_given = Column(Float)

    customer = relationship("DimCustomer", back_populates="orders")
    restaurant = relationship("DimRestaurant", back_populates="orders")
    time_dim = relationship("DimTime", back_populates="orders")
    items = relationship("FactOrderItem", back_populates="order")

class FactOrderItem(Base):
    __tablename__ = "fact_order_items"

    order_item_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("fact_orders.order_id"), index=True)
    item_id = Column(Integer, ForeignKey("dim_food_item.item_id"), index=True)
    quantity = Column(Integer)
    unit_price = Column(Float)
    line_total = Column(Float)

    order = relationship("FactOrder", back_populates="items")
    food_item = relationship("DimFoodItem", back_populates="order_items")

class AnalyticsMarketBasketRule(Base):
    __tablename__ = "analytics_market_basket_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    antecedents = Column(Text, nullable=False, index=True)
    consequents = Column(Text, nullable=False)
    support = Column(Float)
    confidence = Column(Float)
    lift = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AnalyticsRFMSegment(Base):
    __tablename__ = "analytics_rfm_segments"

    customer_id = Column(Integer, ForeignKey("dim_customer.customer_id"), primary_key=True)
    recency = Column(Integer)
    frequency = Column(Integer)
    monetary = Column(Float)
    cluster = Column(Integer)
    segment = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow)
