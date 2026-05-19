"""
Food Delivery Analytics Dashboard — Streamlit App
Run: streamlit run app.py

Tabs:
  1. Overview   — KPIs, revenue trend, city performance
  2. Customers  — RFM segments, retention cohorts, payment methods
  3. Operations — Delivery time, peak hours, on-time performance
  4. SQL Lab    — Run custom SQL queries live (interview killer feature)
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from analytics import (
    build_database, get_conn,
    q_revenue_by_month, q_revenue_by_city, q_top_cuisines,
    q_customer_retention, q_delivery_performance, q_peak_hours,
    q_customer_segments, q_payment_method, q_top_restaurants
)

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "food_analytics.db")

st.set_page_config(
    page_title="Food Delivery Analytics",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Ensure DB exists ──────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    with st.spinner("Building database..."):
        build_database()

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.kpi-card { background:#f8f9fa; border-radius:10px; padding:16px 20px; text-align:center; border: 0.5px solid #e0e0e0; }
.kpi-val  { font-size:28px; font-weight:700; color:#1a1a2e; }
.kpi-lbl  { font-size:12px; color:#666; margin-top:4px; }
.kpi-delta{ font-size:12px; margin-top:2px; }
.seg-chip { display:inline-block; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:500; margin:2px; }
.sql-note { background:#e8f4fd; border-left:3px solid #378add; padding:10px 14px; border-radius:6px; font-size:13px; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

st.title("🍔 Food Delivery Analytics Dashboard")
st.caption("50,000 orders · 5,000 customers · 300 restaurants · 6 cities · SQL-powered")

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    cities = ["All"] + ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"]
    selected_city = st.selectbox("City", cities)
    selected_quarter = st.selectbox("Quarter", ["All", "Q1", "Q2", "Q3", "Q4"])

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Customers", "🚴 Operations", "🔬 SQL Lab"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # KPIs
    conn = get_conn()
    city_filter = f"AND city = '{selected_city}'" if selected_city != "All" else ""
    q_filter    = f"AND quarter = {selected_quarter[1]}" if selected_quarter != "All" else ""

    kpis = pd.read_sql(f"""
        SELECT
            COUNT(order_id)                     AS total_orders,
            ROUND(SUM(final_amount)/1000000, 2) AS gmv_cr,
            ROUND(AVG(final_amount), 0)         AS aov,
            ROUND(SUM(CASE WHEN status='Cancelled'
                      THEN 1.0 ELSE 0 END)
                  / COUNT(*) * 100, 1)          AS cancel_pct,
            COUNT(DISTINCT customer_id)         AS unique_customers,
            ROUND(SUM(discount)/1000000, 2)     AS discount_cr
        FROM orders WHERE 1=1 {city_filter} {q_filter}
    """, conn)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    metrics = [
        ("Total Orders",      f"{kpis['total_orders'][0]:,}",          ""),
        ("GMV",               f"₹{kpis['gmv_cr'][0]}M",               "Gross merchandise value"),
        ("Avg Order Value",   f"₹{kpis['aov'][0]:,.0f}",              ""),
        ("Cancellation Rate", f"{kpis['cancel_pct'][0]}%",             "Lower is better"),
        ("Unique Customers",  f"{kpis['unique_customers'][0]:,}",      ""),
        ("Total Discounts",   f"₹{kpis['discount_cr'][0]}M",          ""),
    ]
    for col, (lbl, val, note) in zip([c1,c2,c3,c4,c5,c6], metrics):
        col.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-val">{val}</div>
          <div class="kpi-lbl">{lbl}</div>
          <div class="kpi-delta" style="color:#888">{note}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Revenue trend
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown("**Monthly revenue trend**")
        df_month = q_revenue_by_month()
        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        df_month["Month"] = df_month["month"].map(month_names)
        st.bar_chart(df_month.set_index("Month")["gross_revenue"])

    with col_b:
        st.markdown("**Revenue by city**")
        df_city = q_revenue_by_city()
        st.bar_chart(df_city.set_index("city")["gross_revenue"])

    # Top cuisines + restaurants
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**Revenue by cuisine**")
        df_cuisine = q_top_cuisines()
        st.bar_chart(df_cuisine.set_index("cuisine")["gross_revenue"])

    with col_d:
        st.markdown("**Top 10 restaurants**")
        df_rest = q_top_restaurants().head(10)[
            ["restaurant_id", "cuisine", "city", "total_orders", "gross_revenue", "avg_delivery_rating"]
        ]
        df_rest.columns = ["ID", "Cuisine", "City", "Orders", "Revenue ₹", "Rating"]
        st.dataframe(df_rest, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**RFM Customer Segments**")
        df_seg = q_customer_segments()
        seg_colors = {
            "Champions":    "#2e7d32",
            "Loyal":        "#1565c0",
            "New customers":"#6a1b9a",
            "At risk":      "#e65100",
            "Hibernating":  "#757575",
        }
        for _, row in df_seg.iterrows():
            color = seg_colors.get(row["segment"], "#333")
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding:10px 14px; border-radius:8px; margin-bottom:8px;
                        background:{color}18; border-left:3px solid {color};">
              <div>
                <span style="font-weight:600; color:{color};">{row['segment']}</span>
                <span style="font-size:12px; color:#666; margin-left:8px;">{row['customer_count']:,} customers</span>
              </div>
              <div style="text-align:right;">
                <span style="font-weight:600;">₹{row['avg_total_spend']:,}</span>
                <span style="font-size:11px; color:#888; display:block;">avg spend · {row['avg_orders']:.1f} orders</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sql-note">
        <b>Interview note:</b> RFM segmentation uses SQL window functions (NTILE).
        Champions = recent + frequent + high spend. At-risk = frequent but lapsed.
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        st.markdown("**Payment method breakdown**")
        df_pay = q_payment_method()
        st.bar_chart(df_pay.set_index("payment_method")["total_orders"])
        st.dataframe(
            df_pay[["payment_method", "total_orders", "avg_order_value", "order_share_pct"]]
            .rename(columns={"payment_method":"Method","total_orders":"Orders",
                             "avg_order_value":"Avg ₹","order_share_pct":"Share %"}),
            use_container_width=True, hide_index=True
        )

    # Cohort retention
    st.markdown("**Customer retention by cohort (monthly)**")
    st.caption("What % of customers from month N are still ordering M months later")
    df_cohort = q_customer_retention()
    pivot = df_cohort.pivot_table(
        index="cohort_month", columns="months_since_first_order",
        values="retention_pct", aggfunc="mean"
    ).round(1)
    pivot.index = pivot.index.map(
        {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
         7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    )
    pivot.columns = [f"M+{c}" for c in pivot.columns]
    st.dataframe(
        pivot.style.background_gradient(cmap="RdYlGn", axis=None, vmin=0, vmax=100),
        use_container_width=True
    )
    st.markdown("""
    <div class="sql-note">
    <b>Interview note:</b> Cohort retention is built with a self-join + window function.
    Green = high retention. This is the #1 most asked DS question at Swiggy/Zomato/PhonePe.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Delivery performance by city**")
        df_del = q_delivery_performance()
        st.dataframe(
            df_del[["city","avg_prep_time","avg_delivery_time","avg_total_time","on_time_pct","avg_rating"]]
            .rename(columns={"city":"City","avg_prep_time":"Prep (min)",
                             "avg_delivery_time":"Delivery (min)","avg_total_time":"Total (min)",
                             "on_time_pct":"On-time %","avg_rating":"Rating"}),
            use_container_width=True, hide_index=True
        )

        st.markdown("**Average total delivery time by city**")
        st.bar_chart(df_del.set_index("city")["avg_total_time"])

    with col_b:
        st.markdown("**Orders by hour of day**")
        df_hours = q_peak_hours()
        st.bar_chart(df_hours.set_index("hour")["total_orders"])

        peak_hour = df_hours.loc[df_hours["total_orders"].idxmax(), "hour"]
        st.info(f"🕐 Peak hour: **{peak_hour}:00** — highest order volume. Used for surge pricing & delivery partner allocation.")

        st.markdown("**Avg order value by hour**")
        st.line_chart(df_hours.set_index("hour")["avg_order_value"])

    # Weekend vs weekday
    st.markdown("**Weekend vs Weekday performance**")
    df_wk = pd.read_sql("""
        SELECT
            CASE WHEN is_weekend=1 THEN 'Weekend' ELSE 'Weekday' END AS day_type,
            COUNT(order_id)                     AS total_orders,
            ROUND(AVG(final_amount), 0)         AS avg_order_value,
            ROUND(SUM(final_amount)/1000, 0)    AS revenue_k,
            ROUND(SUM(CASE WHEN status='Cancelled'
                      THEN 1.0 ELSE 0 END)
                  / COUNT(*) * 100, 1)          AS cancel_pct
        FROM orders
        GROUP BY is_weekend
    """, get_conn())
    df_wk.columns = ["Day Type", "Total Orders", "Avg Order ₹", "Revenue ₹K", "Cancel %"]
    st.dataframe(df_wk, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SQL LAB
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Live SQL Lab")
    st.caption("Write any SQL query against the real database — 4 tables: orders, customers, restaurants, deliveries")

    st.markdown("""
    <div class="sql-note">
    <b>Tables available:</b><br>
    &nbsp;&nbsp;<b>orders</b> — order_id, customer_id, restaurant_id, city, order_date, order_value, final_amount, discount, delivery_fee, payment_method, status, is_weekend, hour, month, quarter<br>
    &nbsp;&nbsp;<b>customers</b> — customer_id, city, age_group, signup_date, is_prime<br>
    &nbsp;&nbsp;<b>restaurants</b> — restaurant_id, city, cuisine, rating, avg_order_value, avg_prep_time_min, is_cloud_kitchen<br>
    &nbsp;&nbsp;<b>deliveries</b> — order_id, prep_time_min, delivery_time_min, total_time_min, delivery_rating, on_time
    </div>
    """, unsafe_allow_html=True)

    # Sample queries
    sample_queries = {
        "Monthly revenue trend": """SELECT month,
       COUNT(order_id)              AS total_orders,
       ROUND(SUM(final_amount), 0)  AS revenue,
       ROUND(AVG(final_amount), 0)  AS avg_order_value
FROM orders
WHERE status = 'Delivered'
GROUP BY month
ORDER BY month""",

        "Customer retention (cohort)": """WITH first_order AS (
    SELECT customer_id, MIN(month) AS cohort_month
    FROM orders WHERE status='Delivered'
    GROUP BY customer_id
)
SELECT f.cohort_month,
       o.month AS order_month,
       COUNT(DISTINCT o.customer_id) AS active_customers
FROM orders o
JOIN first_order f ON o.customer_id = f.customer_id
WHERE o.status = 'Delivered'
GROUP BY f.cohort_month, o.month
ORDER BY f.cohort_month, o.month""",

        "Top cuisines by revenue": """SELECT r.cuisine,
       COUNT(o.order_id)            AS orders,
       ROUND(SUM(o.final_amount),0) AS revenue,
       ROUND(AVG(d.delivery_rating),2) AS avg_rating
FROM orders o
JOIN restaurants r ON o.restaurant_id = r.restaurant_id
LEFT JOIN deliveries d ON o.order_id = d.order_id
WHERE o.status = 'Delivered'
GROUP BY r.cuisine
ORDER BY revenue DESC""",

        "RFM segmentation (window functions)": """SELECT customer_id,
       COUNT(order_id)           AS frequency,
       ROUND(SUM(final_amount),0) AS monetary,
       MAX(month)                AS recency,
       NTILE(4) OVER (ORDER BY COUNT(order_id))      AS f_score,
       NTILE(4) OVER (ORDER BY SUM(final_amount))    AS m_score,
       NTILE(4) OVER (ORDER BY MAX(month) DESC)      AS r_score
FROM orders
WHERE status = 'Delivered'
GROUP BY customer_id
ORDER BY monetary DESC
LIMIT 20""",

        "Peak hours analysis": """SELECT hour,
       COUNT(order_id)              AS total_orders,
       ROUND(AVG(final_amount), 0)  AS avg_order_value,
       SUM(CASE WHEN is_weekend=1 THEN 1 ELSE 0 END) AS weekend_orders
FROM orders
WHERE status = 'Delivered'
GROUP BY hour
ORDER BY hour""",

        "City delivery performance": """SELECT o.city,
       ROUND(AVG(d.prep_time_min), 1)     AS avg_prep,
       ROUND(AVG(d.delivery_time_min), 1) AS avg_delivery,
       ROUND(AVG(d.on_time)*100, 1)       AS on_time_pct,
       ROUND(AVG(d.delivery_rating), 2)   AS avg_rating
FROM deliveries d
JOIN orders o ON d.order_id = o.order_id
GROUP BY o.city
ORDER BY avg_rating DESC""",
    }

    selected_sample = st.selectbox("Load a sample query", ["Custom"] + list(sample_queries.keys()))
    default_sql = sample_queries.get(selected_sample, "SELECT * FROM orders LIMIT 10")

    user_sql = st.text_area("SQL query", value=default_sql, height=180)

    col_run, col_chart = st.columns([1, 4])
    run = col_run.button("▶ Run query", type="primary")
    show_chart = col_chart.checkbox("Show bar chart of first two columns", value=False)

    if run:
        try:
            df_result = pd.read_sql(user_sql, get_conn())
            st.success(f"{len(df_result):,} rows returned")
            st.dataframe(df_result, use_container_width=True, hide_index=True)
            if show_chart and len(df_result.columns) >= 2:
                try:
                    st.bar_chart(df_result.set_index(df_result.columns[0])[df_result.columns[1]])
                except Exception:
                    st.info("Could not render chart — first column must be categorical.")
        except Exception as e:
            st.error(f"SQL error: {e}")

    st.markdown("---")
    st.markdown("**Schema reference**")
    schema_cols = st.columns(4)
    schemas = {
        "orders": ["order_id","customer_id","restaurant_id","city","order_date",
                   "order_value","final_amount","discount","delivery_fee",
                   "payment_method","status","is_weekend","hour","month","quarter"],
        "customers": ["customer_id","city","age_group","signup_date","is_prime"],
        "restaurants": ["restaurant_id","city","cuisine","rating",
                        "avg_order_value","avg_prep_time_min","is_cloud_kitchen"],
        "deliveries": ["order_id","prep_time_min","delivery_time_min",
                       "total_time_min","delivery_rating","on_time"],
    }
    for col, (tbl, cols) in zip(schema_cols, schemas.items()):
        col.markdown(f"**{tbl}**")
        for c in cols:
            col.markdown(f"<span style='font-size:12px;color:#555'>· {c}</span>", unsafe_allow_html=True)
