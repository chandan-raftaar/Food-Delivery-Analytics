"""
Food Delivery Analytics — SQL Query Engine
Uses SQLite so no database setup needed. All analysis via pure SQL.
Interview-ready: every query documented with business reasoning.
"""

import sqlite3
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH  = os.path.join(os.path.dirname(__file__), "data", "food_analytics.db")


# ── BUILD DATABASE ─────────────────────────────────────────────────────────────

def build_database():
    """Load CSVs into SQLite — run once."""
    conn = sqlite3.connect(DB_PATH)
    for table in ["orders", "customers", "restaurants", "deliveries"]:
        df = pd.read_csv(f"{DATA_DIR}/{table}.csv")
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"  Loaded {table}: {len(df):,} rows")
    conn.close()
    print(f"  Database saved → {DB_PATH}")


def get_conn():
    if not os.path.exists(DB_PATH):
        print("Building database...")
        build_database()
    return sqlite3.connect(DB_PATH)


# ── QUERIES ───────────────────────────────────────────────────────────────────

def q_revenue_by_month():
    """Monthly revenue trend — shows seasonality and growth."""
    sql = """
    SELECT
        month,
        COUNT(order_id)                          AS total_orders,
        ROUND(SUM(final_amount), 0)              AS gross_revenue,
        ROUND(AVG(final_amount), 0)              AS avg_order_value,
        ROUND(SUM(CASE WHEN status='Cancelled'
                  THEN 1.0 ELSE 0 END)
              / COUNT(*) * 100, 1)               AS cancellation_pct
    FROM orders
    GROUP BY month
    ORDER BY month
    """
    return pd.read_sql(sql, get_conn())


def q_revenue_by_city():
    """City-level performance — which markets drive the most revenue."""
    sql = """
    SELECT
        city,
        COUNT(order_id)                          AS total_orders,
        ROUND(SUM(final_amount), 0)              AS gross_revenue,
        ROUND(AVG(final_amount), 0)              AS avg_order_value,
        COUNT(DISTINCT customer_id)              AS unique_customers,
        ROUND(SUM(final_amount) /
              COUNT(DISTINCT customer_id), 0)    AS revenue_per_customer
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY city
    ORDER BY gross_revenue DESC
    """
    return pd.read_sql(sql, get_conn())


def q_top_cuisines():
    """Best performing cuisines by revenue and order volume."""
    sql = """
    SELECT
        r.cuisine,
        COUNT(o.order_id)                        AS total_orders,
        ROUND(SUM(o.final_amount), 0)            AS gross_revenue,
        ROUND(AVG(o.final_amount), 0)            AS avg_order_value,
        ROUND(AVG(d.delivery_rating), 2)         AS avg_rating
    FROM orders o
    JOIN restaurants r ON o.restaurant_id = r.restaurant_id
    LEFT JOIN deliveries d ON o.order_id = d.order_id
    WHERE o.status = 'Delivered'
    GROUP BY r.cuisine
    ORDER BY gross_revenue DESC
    """
    return pd.read_sql(sql, get_conn())


def q_customer_retention():
    """
    Customer cohort retention — what % of customers from month N
    are still ordering in subsequent months.
    Interview note: this is one of the most common DS interview questions
    at Swiggy/Zomato/PhonePe.
    """
    sql = """
    WITH first_order AS (
        SELECT customer_id, MIN(month) AS cohort_month
        FROM orders
        WHERE status = 'Delivered'
        GROUP BY customer_id
    ),
    cohort_orders AS (
        SELECT
            f.cohort_month,
            o.month AS order_month,
            COUNT(DISTINCT o.customer_id) AS active_customers
        FROM orders o
        JOIN first_order f ON o.customer_id = f.customer_id
        WHERE o.status = 'Delivered'
        GROUP BY f.cohort_month, o.month
    ),
    cohort_size AS (
        SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
        FROM first_order
        GROUP BY cohort_month
    )
    SELECT
        c.cohort_month,
        co.order_month,
        cs.cohort_customers,
        co.active_customers,
        ROUND(co.active_customers * 100.0 / cs.cohort_customers, 1) AS retention_pct,
        co.order_month - c.cohort_month AS months_since_first_order
    FROM cohort_orders co
    JOIN cohort_size cs ON co.cohort_month = cs.cohort_month
    JOIN (SELECT DISTINCT cohort_month FROM first_order) c
         ON co.cohort_month = c.cohort_month
    ORDER BY c.cohort_month, co.order_month
    """
    return pd.read_sql(sql, get_conn())


def q_delivery_performance():
    """Delivery time analysis by city — operational efficiency metric."""
    sql = """
    SELECT
        o.city,
        ROUND(AVG(d.prep_time_min), 1)           AS avg_prep_time,
        ROUND(AVG(d.delivery_time_min), 1)       AS avg_delivery_time,
        ROUND(AVG(d.total_time_min), 1)          AS avg_total_time,
        ROUND(AVG(d.on_time) * 100, 1)           AS on_time_pct,
        ROUND(AVG(d.delivery_rating), 2)         AS avg_rating,
        COUNT(d.order_id)                        AS delivered_orders
    FROM deliveries d
    JOIN orders o ON d.order_id = o.order_id
    GROUP BY o.city
    ORDER BY avg_total_time ASC
    """
    return pd.read_sql(sql, get_conn())


def q_peak_hours():
    """Order volume by hour — used for surge pricing and staffing decisions."""
    sql = """
    SELECT
        hour,
        COUNT(order_id)                          AS total_orders,
        ROUND(AVG(final_amount), 0)              AS avg_order_value,
        ROUND(SUM(CASE WHEN is_weekend=1
                  THEN 1.0 ELSE 0 END)
              / COUNT(*) * 100, 1)               AS weekend_pct
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY hour
    ORDER BY hour
    """
    return pd.read_sql(sql, get_conn())


def q_customer_segments():
    """
    RFM-style customer segmentation using window functions.
    R = Recency (last order month), F = Frequency, M = Monetary value.
    """
    sql = """
    WITH customer_stats AS (
        SELECT
            customer_id,
            COUNT(order_id)                      AS order_count,
            ROUND(SUM(final_amount), 0)          AS total_spend,
            ROUND(AVG(final_amount), 0)          AS avg_order_value,
            MAX(month)                           AS last_order_month,
            MIN(month)                           AS first_order_month
        FROM orders
        WHERE status = 'Delivered'
        GROUP BY customer_id
    ),
    scored AS (
        SELECT *,
            NTILE(4) OVER (ORDER BY last_order_month DESC) AS recency_score,
            NTILE(4) OVER (ORDER BY order_count)           AS frequency_score,
            NTILE(4) OVER (ORDER BY total_spend)           AS monetary_score
        FROM customer_stats
    )
    SELECT
        CASE
            WHEN recency_score=4 AND frequency_score>=3 THEN 'Champions'
            WHEN recency_score>=3 AND frequency_score>=3 THEN 'Loyal'
            WHEN recency_score=4 AND frequency_score<=2 THEN 'New customers'
            WHEN recency_score<=2 AND frequency_score>=3 THEN 'At risk'
            ELSE 'Hibernating'
        END                                      AS segment,
        COUNT(*)                                 AS customer_count,
        ROUND(AVG(total_spend), 0)               AS avg_total_spend,
        ROUND(AVG(order_count), 1)               AS avg_orders,
        ROUND(AVG(avg_order_value), 0)           AS avg_order_value
    FROM scored
    GROUP BY segment
    ORDER BY avg_total_spend DESC
    """
    return pd.read_sql(sql, get_conn())


def q_payment_method():
    """Payment method breakdown — useful for fintech partnerships."""
    sql = """
    SELECT
        payment_method,
        COUNT(order_id)                          AS total_orders,
        ROUND(SUM(final_amount), 0)              AS gross_revenue,
        ROUND(AVG(final_amount), 0)              AS avg_order_value,
        ROUND(COUNT(*) * 100.0 /
              SUM(COUNT(*)) OVER (), 1)          AS order_share_pct
    FROM orders
    WHERE status = 'Delivered'
    GROUP BY payment_method
    ORDER BY total_orders DESC
    """
    return pd.read_sql(sql, get_conn())


def q_top_restaurants():
    """Top restaurants by revenue with rating and delivery performance."""
    sql = """
    SELECT
        r.restaurant_id,
        r.cuisine,
        r.city,
        r.rating                                 AS restaurant_rating,
        COUNT(o.order_id)                        AS total_orders,
        ROUND(SUM(o.final_amount), 0)            AS gross_revenue,
        ROUND(AVG(d.total_time_min), 0)          AS avg_delivery_time,
        ROUND(AVG(d.delivery_rating), 2)         AS avg_delivery_rating
    FROM restaurants r
    JOIN orders o ON r.restaurant_id = o.restaurant_id
    LEFT JOIN deliveries d ON o.order_id = d.order_id
    WHERE o.status = 'Delivered'
    GROUP BY r.restaurant_id
    ORDER BY gross_revenue DESC
    LIMIT 20
    """
    return pd.read_sql(sql, get_conn())


# ── MAIN — print key insights ──────────────────────────────────────────────────

def run_analysis():
    print("=" * 60)
    print("FOOD DELIVERY ANALYTICS — KEY INSIGHTS")
    print("=" * 60)

    print("\n1. Revenue by city (top 3):")
    df = q_revenue_by_city().head(3)
    for _, r in df.iterrows():
        print(f"   {r['city']:12s} ₹{r['gross_revenue']:,.0f}  ({r['total_orders']:,} orders)")

    print("\n2. Top cuisines by revenue:")
    df = q_top_cuisines().head(5)
    for _, r in df.iterrows():
        print(f"   {r['cuisine']:15s} ₹{r['gross_revenue']:,.0f}")

    print("\n3. Delivery performance:")
    df = q_delivery_performance()
    print(f"   Avg total time : {df['avg_total_time'].mean():.0f} min")
    print(f"   On-time rate   : {df['on_time_pct'].mean():.1f}%")
    print(f"   Avg rating     : {df['avg_rating'].mean():.2f}/5")

    print("\n4. Customer segments:")
    df = q_customer_segments()
    for _, r in df.iterrows():
        print(f"   {r['segment']:15s} {r['customer_count']:,} customers  avg spend ₹{r['avg_total_spend']:,}")

    print("\n5. Peak order hour:", q_peak_hours().loc[q_peak_hours()['total_orders'].idxmax(), 'hour'], ":00")

    print("\nDatabase ready. Run: streamlit run app.py")


if __name__ == "__main__":
    build_database()
    run_analysis()
