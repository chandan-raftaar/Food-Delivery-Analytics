"""
Generates a realistic food delivery dataset (Swiggy/Zomato style).
Saves 4 tables as CSVs: orders, customers, restaurants, deliveries.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

OUTPUT_DIR = os.path.dirname(__file__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
N_CUSTOMERS    = 5000
N_RESTAURANTS  = 300
N_ORDERS       = 50000
START_DATE     = datetime(2023, 1, 1)
END_DATE       = datetime(2024, 12, 31)

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]
CITY_WEIGHTS = [0.30, 0.25, 0.20, 0.12, 0.08, 0.05]

CUISINES = ["North Indian", "South Indian", "Chinese", "Pizza", "Biryani",
            "Burger", "Desserts", "Healthy", "Thai", "Continental"]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Wallet"]
PAYMENT_WEIGHTS = [0.45, 0.20, 0.15, 0.12, 0.08]

# ── CUSTOMERS ─────────────────────────────────────────────────────────────────
customer_ids = [f"C{i:05d}" for i in range(N_CUSTOMERS)]
customer_cities = np.random.choice(CITIES, size=N_CUSTOMERS, p=CITY_WEIGHTS)
customer_signup = [
    START_DATE + timedelta(days=np.random.randint(0, 365))
    for _ in range(N_CUSTOMERS)
]
customer_age = np.random.choice(
    ["18-24", "25-34", "35-44", "45+"],
    size=N_CUSTOMERS, p=[0.30, 0.45, 0.18, 0.07]
)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "city": customer_cities,
    "age_group": customer_age,
    "signup_date": customer_signup,
    "is_prime": np.random.choice([0, 1], size=N_CUSTOMERS, p=[0.65, 0.35]),
})

# ── RESTAURANTS ───────────────────────────────────────────────────────────────
restaurant_ids = [f"R{i:04d}" for i in range(N_RESTAURANTS)]
restaurant_cities = np.random.choice(CITIES, size=N_RESTAURANTS, p=CITY_WEIGHTS)
restaurant_cuisine = np.random.choice(CUISINES, size=N_RESTAURANTS)
restaurant_rating = np.random.normal(3.9, 0.4, N_RESTAURANTS).clip(2.5, 5.0).round(1)
restaurant_avg_price = np.random.choice(
    [150, 200, 250, 300, 400, 500],
    size=N_RESTAURANTS,
    p=[0.10, 0.25, 0.30, 0.20, 0.10, 0.05]
)
restaurant_prep_time = np.random.randint(15, 45, N_RESTAURANTS)

restaurants = pd.DataFrame({
    "restaurant_id": restaurant_ids,
    "city": restaurant_cities,
    "cuisine": restaurant_cuisine,
    "rating": restaurant_rating,
    "avg_order_value": restaurant_avg_price,
    "avg_prep_time_min": restaurant_prep_time,
    "is_cloud_kitchen": np.random.choice([0, 1], size=N_RESTAURANTS, p=[0.60, 0.40]),
})

# ── ORDERS ────────────────────────────────────────────────────────────────────
order_ids = [f"ORD{i:07d}" for i in range(N_ORDERS)]

# Time-based patterns — more orders on weekends and evenings
order_dates = []
for _ in range(N_ORDERS):
    day_offset = np.random.randint(0, (END_DATE - START_DATE).days)
    raw = [1,1,1,1,1,1,2,3,4,3,3,4,6,5,4,4,5,6,8,8,7,6,5,4]
    total = sum(raw)
    p_hour = [x/total for x in raw]
    hour = np.random.choice(range(24), p=p_hour)
    order_dates.append(START_DATE + timedelta(days=int(day_offset), hours=int(hour)))

order_customers = np.random.choice(customer_ids, size=N_ORDERS)
order_restaurants = np.random.choice(restaurant_ids, size=N_ORDERS)

# Match restaurant city to customer city 70% of time
order_cities = []
for cid in order_customers:
    if np.random.random() < 0.70:
        order_cities.append(customers.loc[customers.customer_id == cid, "city"].values[0])
    else:
        order_cities.append(np.random.choice(CITIES, p=CITY_WEIGHTS))

# Order value based on restaurant avg price ± noise
order_values = []
for rid in order_restaurants:
    base = restaurants.loc[restaurants.restaurant_id == rid, "avg_order_value"].values[0]
    order_values.append(max(80, base + np.random.normal(0, 50)))
order_values = np.round(order_values, 2)

delivery_fee = np.where(order_values > 300, 0, np.random.choice([20, 30, 40, 49], size=N_ORDERS))
discount = np.random.choice([0, 0, 0, 30, 50, 75, 100], size=N_ORDERS)
final_amount = np.maximum(order_values + delivery_fee - discount, 80).round(2)

status = np.random.choice(
    ["Delivered", "Cancelled", "Delivered", "Delivered", "Delivered"],
    size=N_ORDERS
)

orders = pd.DataFrame({
    "order_id": order_ids,
    "customer_id": order_customers,
    "restaurant_id": order_restaurants,
    "city": [order_cities[i] for i in range(N_ORDERS)],
    "order_date": order_dates,
    "order_value": order_values,
    "delivery_fee": delivery_fee,
    "discount": discount,
    "final_amount": final_amount,
    "payment_method": np.random.choice(PAYMENT_METHODS, size=N_ORDERS, p=PAYMENT_WEIGHTS),
    "status": status,
    "is_weekend": [1 if d.weekday() >= 5 else 0 for d in order_dates],
    "hour": [d.hour for d in order_dates],
    "month": [d.month for d in order_dates],
    "quarter": [((d.month - 1) // 3) + 1 for d in order_dates],
})

# ── DELIVERIES ────────────────────────────────────────────────────────────────
delivered_orders = orders[orders["status"] == "Delivered"]["order_id"].values

prep_times = []
delivery_times = []
ratings = []
for oid in delivered_orders:
    rid = orders.loc[orders.order_id == oid, "restaurant_id"].values[0]
    base_prep = restaurants.loc[restaurants.restaurant_id == rid, "avg_prep_time_min"].values[0]
    prep = max(10, base_prep + np.random.normal(0, 5))
    delivery = max(10, np.random.normal(28, 8))
    prep_times.append(round(prep, 1))
    delivery_times.append(round(delivery, 1))
    ratings.append(np.random.choice([1, 2, 3, 4, 5], p=[0.03, 0.05, 0.12, 0.35, 0.45]))

deliveries = pd.DataFrame({
    "order_id": delivered_orders,
    "prep_time_min": prep_times,
    "delivery_time_min": delivery_times,
    "total_time_min": [p + d for p, d in zip(prep_times, delivery_times)],
    "delivery_rating": ratings,
    "on_time": [1 if t <= 45 else 0 for t in [p + d for p, d in zip(prep_times, delivery_times)]],
})

# ── SAVE ──────────────────────────────────────────────────────────────────────
customers.to_csv(f"{OUTPUT_DIR}/customers.csv", index=False)
restaurants.to_csv(f"{OUTPUT_DIR}/restaurants.csv", index=False)
orders.to_csv(f"{OUTPUT_DIR}/orders.csv", index=False)
deliveries.to_csv(f"{OUTPUT_DIR}/deliveries.csv", index=False)

print(f"customers   : {len(customers):,} rows")
print(f"restaurants : {len(restaurants):,} rows")
print(f"orders      : {len(orders):,} rows")
print(f"deliveries  : {len(deliveries):,} rows")
print(f"Avg order value : ₹{orders['final_amount'].mean():.0f}")
print(f"Cancellation rate: {(orders['status']=='Cancelled').mean():.1%}")
print(f"On-time delivery : {deliveries['on_time'].mean():.1%}")
print("All CSVs saved to data/")
