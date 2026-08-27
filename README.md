# MaxiFoods — Full-Stack Food Delivery Analytics Web Application

A full-stack web application for food delivery customer intelligence, featuring **FastAPI**, **PostgreSQL**, **JWT Authentication**, scheduled Apriori & RFM mining jobs, live SQL analytics, and an interactive dark warm HTML5/JS frontend matching the design system.

---

## 🌟 Architecture Overview

- **Backend**: Python 3.13 + FastAPI REST API
- **Database**: PostgreSQL star schema (`dim_customer`, `dim_restaurant`, `dim_food_item`, `dim_time`, `fact_orders`, `fact_order_items`)
- **Authentication**: JWT Bearer sessions + Bcrypt password hashing (`users` table with role-based access control)
- **Data Mining & Analytics**: 
  - Scheduled background job using `mlxtend` (Apriori Market Basket association rules) and `scikit-learn` (RFM K-Means customer segmentation) writing into PostgreSQL analytics tables (`analytics_market_basket_rules`, `analytics_rfm_segments`).
  - Live SQL aggregation queries computing per-restaurant KPIs (order volume, repeat customers, delivery time, veg order share, time of day / day of week demand, top items, monthly revenue trends).
- **Frontend**: Responsive single-page web app with Fraunces / Inter / IBM Plex Mono typography, mood/diet filter chips, live pairing recommendations, owner KPI strip, and Chart.js graphics.

---

## 🚀 Quick Start Setup Instructions

### 1. Prerequisites
- **Python 3.10+** installed
- **PostgreSQL 12+** service running on `localhost:5432`

### 2. Environment Setup & Dependencies
Install the required backend dependencies:

```bash
pip install -r backend/requirements.txt
```

### 3. PostgreSQL Database Configuration
By default, the application connects to PostgreSQL on `localhost:5432` with username `postgres` and password `postgres`.

If your local PostgreSQL credentials differ, you can set the following environment variables before running commands:

```bash
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="your_password"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_DB="maxifoods"
```

### 4. Database Initialization & Seeding
Run the database seed script to automatically create the `maxifoods` database, create all star-schema tables, load `data/*.csv`, run initial Apriori/RFM jobs, and seed sample user accounts:

```bash
python -m backend.app.seed
```

### 5. Start the FastAPI Server
Launch the backend server (which also serves the frontend):

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 6. Access the Application
Open your browser and navigate to:

👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🔐 Sample Accounts & Demo Logins

You can create a new account via the **Create Account** tab or use any of the pre-seeded demo accounts (single-click buttons are also provided on the sign-in page):

### Demo Customer Account
- **Email**: `customer@maxifoods.com`
- **Password**: `password123`

### Demo Restaurant Owner Accounts (10 Sample Restaurants)
- **Password for all owner accounts**: `password123`

| Owner Email | Linked Restaurant | City |
| :--- | :--- | :--- |
| `owner1@maxifoods.com` | The Veg Table | Pune |
| `owner2@maxifoods.com` | Green Bowl Kitchen | Delhi |
| `owner3@maxifoods.com` | Sweet Ending Desserts | Bangalore |
| `owner4@maxifoods.com` | Kebab Junction | Bangalore |
| `owner5@maxifoods.com` | Curry Culture | Bangalore |
| `owner6@maxifoods.com` | Grill & Chill | Mumbai |
| `owner7@maxifoods.com` | Andhra Mess | Mumbai |
| `owner8@maxifoods.com` | Punjabi Tadka | Hyderabad |
| `owner9@maxifoods.com` | Spice Route | Mumbai |
| `owner10@maxifoods.com` | Royal Biryani House | Hyderabad |

---

## 📡 REST API Endpoints

- `POST /api/auth/signup` — Register new user account (`customer` or `restaurant_owner`).
- `POST /api/auth/login` — Authenticate user, return JWT token.
- `GET /api/auth/me` — Return current authenticated user info.
- `GET /api/recommendations?mood=&diet=` — Live customer dish recommendations with serving restaurants and Apriori pairing rules.
- `GET /api/restaurants` — List of top restaurants for owner dashboard selector.
- `GET /api/restaurants/:id/analytics` — Live SQL calculated KPIs (total orders, repeat customers, delivery time, veg split, hourly/weekday demand, monthly trend).

---

## 🔄 Scheduled Analytics Job

The Apriori market basket mining and RFM segmentation pipeline can be triggered manually at any time:

```bash
python -m backend.app.analytics_job
```

When the FastAPI server is running, `APScheduler` automatically executes this job periodically in the background to ensure analytics tables remain fresh.
