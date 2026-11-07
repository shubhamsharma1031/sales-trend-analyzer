"""
Generate a realistic sample retail sales dataset for an Indian company (2023-2024).

The data is synthetic (no real customers), but it follows realistic patterns:
- festive-season peak in October-November (Diwali) and a smaller March peak (financial year end)
- different margins per category, discounts that reduce profit
- regional differences across Indian states

To practise data cleaning, the raw file also contains common real-world problems:
duplicate rows, missing values, inconsistent text casing and extra spaces.

Run:  python data/generate_data.py
Output: data/raw/sales_raw.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_ORDERS = 5000
START, END = "2023-01-01", "2024-12-31"

rng = np.random.default_rng(SEED)

REGIONS = {
    "North": [("Delhi", "New Delhi"), ("Uttar Pradesh", "Lucknow"), ("Punjab", "Ludhiana"), ("Haryana", "Gurugram")],
    "West": [("Maharashtra", "Mumbai"), ("Maharashtra", "Pune"), ("Gujarat", "Ahmedabad"), ("Rajasthan", "Jaipur")],
    "South": [("Karnataka", "Bengaluru"), ("Tamil Nadu", "Chennai"), ("Telangana", "Hyderabad"), ("Kerala", "Kochi")],
    "East": [("West Bengal", "Kolkata"), ("Odisha", "Bhubaneswar"), ("Bihar", "Patna"), ("Assam", "Guwahati")],
    "Central": [("Madhya Pradesh", "Indore"), ("Madhya Pradesh", "Bhopal"), ("Chhattisgarh", "Raipur")],
}
REGION_WEIGHTS = {"North": 0.24, "West": 0.28, "South": 0.25, "East": 0.13, "Central": 0.10}

# category -> list of (sub_category, product, base unit price in INR, cost ratio)
CATALOG = {
    "Electronics": [
        ("Phones", "Smartphone 5G 128GB", 18999, 0.82),
        ("Phones", "Feature Phone Dual SIM", 1499, 0.78),
        ("Accessories", "Wireless Earbuds", 2499, 0.60),
        ("Accessories", "Power Bank 20000mAh", 1799, 0.62),
        ("Computers", "Laptop i5 16GB", 58999, 0.86),
        ("Computers", "Wireless Mouse", 699, 0.55),
    ],
    "Furniture": [
        ("Chairs", "Ergonomic Office Chair", 8999, 0.70),
        ("Tables", "Study Table Engineered Wood", 6499, 0.72),
        ("Storage", "Bookshelf 5 Tier", 4299, 0.68),
        ("Furnishings", "Table Lamp LED", 1199, 0.58),
    ],
    "Office Supplies": [
        ("Paper", "A4 Paper Ream 500 Sheets", 349, 0.65),
        ("Binders", "Ring Binder Pack of 4", 299, 0.52),
        ("Art", "Gel Pen Set of 10", 199, 0.48),
        ("Storage", "File Organizer", 549, 0.55),
    ],
    "Clothing": [
        ("Men", "Cotton Shirt", 1299, 0.50),
        ("Women", "Kurta Set", 1899, 0.48),
        ("Footwear", "Running Shoes", 2999, 0.58),
        ("Accessories", "Leather Wallet", 799, 0.45),
    ],
}
CATEGORY_WEIGHTS = {"Electronics": 0.30, "Furniture": 0.18, "Office Supplies": 0.27, "Clothing": 0.25}
SEGMENTS = ["Consumer", "Corporate", "Small Business"]
SEGMENT_WEIGHTS = [0.55, 0.28, 0.17]
SHIP_MODES = ["Standard", "Express", "Same Day"]
SHIP_DAYS = {"Standard": (4, 7), "Express": (2, 3), "Same Day": (0, 0)}

# relative demand by month (festive season and financial-year-end peaks)
MONTH_FACTOR = {1: 0.80, 2: 0.85, 3: 1.15, 4: 0.90, 5: 0.90, 6: 0.85,
                7: 0.88, 8: 0.95, 9: 1.00, 10: 1.45, 11: 1.40, 12: 1.10}


def pick(options, weights):
    return options[rng.choice(len(options), p=np.array(weights) / sum(weights))]


def random_dates(n):
    days = pd.date_range(START, END, freq="D")
    month_w = np.array([MONTH_FACTOR[d.month] for d in days])
    year_w = np.where(days.year == 2024, 1.12, 1.0)  # ~12% year-on-year growth
    w = month_w * year_w
    return pd.Series(rng.choice(days, size=n, p=w / w.sum())).sort_values().reset_index(drop=True)


def build():
    order_dates = random_dates(N_ORDERS)
    customers = [f"CUST-{i:04d}" for i in range(1, 901)]
    rows = []
    for i, order_date in enumerate(order_dates, start=1):
        region = pick(list(REGION_WEIGHTS), list(REGION_WEIGHTS.values()))
        state, city = REGIONS[region][rng.integers(len(REGIONS[region]))]
        category = pick(list(CATEGORY_WEIGHTS), list(CATEGORY_WEIGHTS.values()))
        sub_cat, product, base_price, cost_ratio = CATALOG[category][rng.integers(len(CATALOG[category]))]
        segment = pick(SEGMENTS, SEGMENT_WEIGHTS)
        ship_mode = pick(SHIP_MODES, [0.70, 0.22, 0.08])
        lo, hi = SHIP_DAYS[ship_mode]
        ship_date = order_date + pd.Timedelta(days=int(rng.integers(lo, hi + 1)))

        quantity = int(rng.integers(1, 6 if base_price < 5000 else 3))
        if segment != "Consumer" and category == "Office Supplies":
            quantity *= int(rng.integers(2, 6))  # businesses buy supplies in bulk
        unit_price = round(base_price * rng.uniform(0.95, 1.05), 2)

        festive = order_date.month in (10, 11)
        discount = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20, 0.30],
                                    p=[0.25, 0.20, 0.20, 0.15, 0.12, 0.08] if festive
                                    else [0.45, 0.20, 0.15, 0.10, 0.07, 0.03]))
        sales = round(quantity * unit_price * (1 - discount), 2)
        cost = round(quantity * base_price * cost_ratio, 2)
        profit = round(sales - cost, 2)

        rows.append({
            "order_id": f"ORD-{order_date.year}-{i:05d}",
            "order_date": order_date.strftime("%Y-%m-%d"),
            "ship_date": ship_date.strftime("%Y-%m-%d"),
            "ship_mode": ship_mode,
            "customer_id": customers[rng.integers(len(customers))],
            "segment": segment,
            "region": region,
            "state": state,
            "city": city,
            "category": category,
            "sub_category": sub_cat,
            "product_name": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": discount,
            "sales": sales,
            "cost": cost,
            "profit": profit,
        })
    return pd.DataFrame(rows)


def add_data_quality_issues(df):
    """Inject typical problems so the cleaning step has real work to do."""
    df = df.copy()
    n = len(df)
    # 1) ~1% exact duplicate rows
    dupes = df.sample(n=int(n * 0.01), random_state=SEED)
    df = pd.concat([df, dupes], ignore_index=True)
    # 2) inconsistent casing / extra spaces in text columns
    idx = rng.choice(len(df), size=int(len(df) * 0.04), replace=False)
    df.loc[idx, "region"] = df.loc[idx, "region"].str.upper()
    idx = rng.choice(len(df), size=int(len(df) * 0.03), replace=False)
    df.loc[idx, "category"] = "  " + df.loc[idx, "category"].str.lower() + " "
    idx = rng.choice(len(df), size=int(len(df) * 0.02), replace=False)
    df.loc[idx, "city"] = df.loc[idx, "city"] + "  "
    # 3) missing values
    for col, share in [("segment", 0.015), ("ship_mode", 0.01), ("discount", 0.01)]:
        idx = rng.choice(len(df), size=int(len(df) * share), replace=False)
        df.loc[idx, col] = np.nan
    # 4) a few rows with missing sales that can be recalculated
    idx = rng.choice(len(df), size=25, replace=False)
    df.loc[idx, "sales"] = np.nan
    # 5) shuffle so problems are spread out
    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "raw" / "sales_raw.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = add_data_quality_issues(build())
    raw.to_csv(out, index=False)
    print(f"Saved {len(raw):,} rows to {out}")
