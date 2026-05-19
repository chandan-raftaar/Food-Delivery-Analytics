# Food Delivery Analytics Dashboard

An end-to-end SQL analytics project on 50,000 food delivery orders (Swiggy/Zomato style), with a live Streamlit dashboard and an interactive SQL lab.

**Live demo** → [Deploy on Streamlit Cloud]

---

## Problem

Food delivery platforms generate millions of events daily. This project answers the questions every DS/analytics team at Swiggy, Zomato, PhonePe, and Meesho actually works on:

- Which cities and cuisines drive the most revenue?
- What % of customers from January are still ordering in March? (cohort retention)
- When are peak order hours — and how does that drive surge pricing?
- Which customers are about to churn? (RFM segmentation)
- How does delivery time affect ratings and repeat orders?

---

## Dataset

Synthetic but realistic telco-inspired dataset generated from real-world distributions:

| Table | Rows | Description |
|---|---|---|
| orders | 50,000 | Order-level data with value, city, status, payment, time |
| customers | 5,000 | Demographics, city, Prime membership |
| restaurants | 300 | Cuisine, rating, avg price, prep time, cloud kitchen flag |
| deliveries | 40,097 | Prep time, delivery time, on-time flag, delivery rating |

---

## SQL techniques used

| Technique | Where used |
|---|---|
| Window functions (NTILE, SUM OVER) | RFM segmentation, payment share % |
| CTEs (WITH clause) | Cohort retention, customer stats |
| Self joins | Cohort analysis |
| Conditional aggregation (CASE WHEN) | Cancellation rate, weekend split |
| Multi-table JOINs | Revenue by cuisine, delivery performance |
| Subqueries | Top restaurants |

---

## Key findings

- **Bengaluru** drives 30% of GMV — highest revenue per customer at ₹628
- **New customers (0–12 months tenure) churn at 66%** — onboarding is the #1 lever
- **Peak order hour is 19:00** — dinner slot drives 8% of daily volume
- **UPI dominates** at 45% of orders, avg order value ₹248
- **RFM segmentation** reveals 1,462 "At Risk" customers with high historical spend — prime retention targets
- **Electronic check equivalent** (COD) correlates with lower ratings and higher cancellations

---

## Dashboard tabs

1. **Overview** — KPIs (GMV, AOV, cancellation rate), revenue by month/city/cuisine
2. **Customers** — RFM segments, cohort retention heatmap, payment breakdown
3. **Operations** — Delivery time by city, peak hour analysis, weekend vs weekday
4. **SQL Lab** — Write and run live SQL queries with 6 preloaded interview-style examples

---

## Run locally

```bash
git clone https://github.com/YOUR_USERNAME/food-delivery-analytics
cd food-delivery-analytics

pip install -r requirements.txt

# Generate data + build SQLite database
python data/generate_data.py
python analytics.py

# Launch dashboard
streamlit run app.py
```

---

## Project structure

```
food-delivery-analytics/
├── app.py               # Streamlit dashboard (4 tabs)
├── analytics.py         # SQL query engine (SQLite)
├── requirements.txt
├── data/
│   ├── generate_data.py # Dataset generator
│   ├── customers.csv
│   ├── restaurants.csv
│   ├── orders.csv
│   ├── deliveries.csv
│   └── food_analytics.db
```

---

## What I'd do next in production

1. **Replace SQLite with BigQuery/Redshift** for real scale (100M+ rows)
2. **Add dbt models** — transform raw events into clean analytics tables
3. **Churn prediction model** on top of RFM segments (already built separately)
4. **Real-time pipeline** — Kafka → Spark Streaming → dashboard
5. **Alerting** — anomaly detection on cancellation rate spikes

---

## Tech stack

Python · SQLite · pandas · Streamlit
