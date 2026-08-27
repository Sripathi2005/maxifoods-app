from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

# Auth Schemas
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "customer"
    restaurant_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    restaurant_id: Optional[int] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Recommendation Schemas
class ServingRestaurant(BaseModel):
    restaurant_id: int
    restaurant_name: str
    city: str
    avg_rating: float
    current_offer: Optional[str] = None

class RecommendationItem(BaseModel):
    item_id: int
    item_name: str
    category: str
    veg_flag: str
    price: float
    moods: List[str]
    restaurants: List[ServingRestaurant]
    pairs_well_with: Optional[str] = None
    pairing_confidence: Optional[float] = None

# Restaurant Analytics Schemas
class RestaurantKPIs(BaseModel):
    total_orders: int
    avg_items_per_order: float
    avg_delivery_time: float
    avg_rating_given: float
    veg_order_pct: float
    repeat_customers: int

class TopItem(BaseModel):
    item_name: str
    quantity: int

class VegSplitItem(BaseModel):
    veg_flag: str
    quantity: int

class MonthlyOrderItem(BaseModel):
    month_year: str
    order_count: int

class SeasonVegTrendItem(BaseModel):
    veg_season_tag: str
    veg_pct: float

class MonthlyVegSplitItem(BaseModel):
    month_year: str
    veg_flag: str
    quantity: int

class RestaurantAnalyticsResponse(BaseModel):
    restaurant_id: int
    restaurant_name: str
    city: str
    cuisine: str
    avg_rating: float
    current_offer: Optional[str] = None
    kpis: RestaurantKPIs
    demand_by_time_slot: Dict[str, int]
    demand_by_weekday: Dict[str, int]
    top_items: List[TopItem]
    veg_split: List[VegSplitItem]
    monthly_orders: List[MonthlyOrderItem]
    season_veg_trend: List[SeasonVegTrendItem]
    monthly_veg_split: List[MonthlyVegSplitItem] = []

class RestaurantListItem(BaseModel):
    restaurant_id: int
    restaurant_name: str
    city: str
    primary_cuisine: str
    avg_rating: float
    current_offer: Optional[str] = None
