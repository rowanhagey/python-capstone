"""
Builds a sample SQLite database with revenue, churn, and regional performance
data so the Quantitative Agent has something realistic to query.

Run: python data/build_sql_db.py
"""
import sqlite3
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "enterprise.db")


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE monthly_revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,      -- 'YYYY-MM'
            region TEXT NOT NULL,
            revenue REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            signup_month TEXT NOT NULL,
            churn_month TEXT,          -- NULL if still active
            plan TEXT NOT NULL
        )
    """)

    regions = ["North America", "EMEA", "APAC", "LATAM"]
    plans = ["Basic", "Pro", "Enterprise"]
    months = [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 9)]

    random.seed(42)

    # Revenue: base per region with growth trend + noise
    base_revenue = {"North America": 180000, "EMEA": 120000, "APAC": 90000, "LATAM": 45000}
    for i, month in enumerate(months):
        for region in regions:
            growth = 1 + (i * 0.015)
            noise = random.uniform(0.92, 1.08)
            revenue = round(base_revenue[region] * growth * noise, 2)
            cur.execute(
                "INSERT INTO monthly_revenue (month, region, revenue) VALUES (?, ?, ?)",
                (month, region, revenue),
            )

    # Customers with churn
    customer_id = 1
    for month in months:
        for region in regions:
            n_signups = random.randint(15, 40)
            for _ in range(n_signups):
                plan = random.choices(plans, weights=[0.5, 0.35, 0.15])[0]
                churn_month = None
                if random.random() < 0.12:
                    signup_idx = months.index(month)
                    churn_idx = min(signup_idx + random.randint(1, 6), len(months) - 1)
                    if churn_idx > signup_idx:
                        churn_month = months[churn_idx]
                cur.execute(
                    "INSERT INTO customers (region, signup_month, churn_month, plan) VALUES (?, ?, ?, ?)",
                    (region, month, churn_month, plan),
                )
                customer_id += 1

    conn.commit()
    conn.close()
    print(f"Built database at {DB_PATH}")
    print(f"  monthly_revenue rows: {len(months) * len(regions)}")


if __name__ == "__main__":
    build()

