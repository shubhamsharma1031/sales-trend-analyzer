"""
Clean the raw sales file and produce an analysis-ready dataset.

Steps
1. Standardise text columns (trim spaces, fix casing)
2. Remove duplicate orders (exact copies and copies with a missing value)
3. Fix data types (dates, numbers)
4. Handle missing values:
   - discount: recalculate from sales / (quantity x unit_price) where possible, else 0
   - sales: recalculate from quantity x unit_price x (1 - discount)
   - ship_mode: infer from the number of shipping days
   - segment: fill with "Unknown"
5. Recalculate profit and add helper columns (year, month, margin, shipping days)
6. Validate the result and save it

Run:  python src/clean_data.py
Input:  data/raw/sales_raw.csv
Output: data/clean/sales_clean.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sales_raw.csv"
CLEAN = ROOT / "data" / "clean" / "sales_clean.csv"

TEXT_COLS = ["ship_mode", "segment", "region", "state", "city", "category", "sub_category", "product_name"]


def standardise_text(df):
    for col in TEXT_COLS:
        df[col] = df[col].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    # Title case for label columns ("NORTH" -> "North", "office supplies" -> "Office Supplies")
    for col in ["region", "category"]:
        df[col] = df[col].str.title()
    return df


def infer_ship_mode(days):
    if pd.isna(days):
        return pd.NA
    if days == 0:
        return "Same Day"
    if days <= 3:
        return "Express"
    return "Standard"


def clean(raw):
    report = {"rows_in": len(raw)}
    df = standardise_text(raw.copy())

    before = len(df)
    df = df.drop_duplicates()
    # Some duplicates are not exact copies (one copy has a missing value).
    # Keep the most complete row for each order_id.
    df = (df.assign(_nulls=df.isna().sum(axis=1))
            .sort_values("_nulls")
            .drop_duplicates(subset="order_id", keep="first")
            .drop(columns="_nulls"))
    report["duplicates_removed"] = before - len(df)

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")
    for col in ["quantity", "unit_price", "discount", "sales", "cost", "profit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    report["missing_before"] = df.isna().sum()[lambda s: s > 0].to_dict()

    gross = df["quantity"] * df["unit_price"]
    # discount: recover from sales where sales is known
    mask = df["discount"].isna() & df["sales"].notna()
    df.loc[mask, "discount"] = (1 - df.loc[mask, "sales"] / gross[mask]).clip(0, 1).round(2)
    df["discount"] = df["discount"].fillna(0)
    # sales: recalculate where missing
    mask = df["sales"].isna()
    df.loc[mask, "sales"] = (gross[mask] * (1 - df.loc[mask, "discount"])).round(2)

    df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days
    mask = df["ship_mode"].isna()
    df.loc[mask, "ship_mode"] = df.loc[mask, "shipping_days"].apply(infer_ship_mode)
    df["segment"] = df["segment"].fillna("Unknown")

    df["profit"] = (df["sales"] - df["cost"]).round(2)
    df["profit_margin"] = np.where(df["sales"] > 0, (df["profit"] / df["sales"]).round(4), 0)
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["month_name"] = df["order_date"].dt.strftime("%b")
    df["order_period"] = df["order_date"].dt.strftime("%Y-%m")

    report["missing_after"] = int(df.isna().sum().sum())
    report["rows_out"] = len(df)
    return df.sort_values("order_date").reset_index(drop=True), report


def validate(df):
    assert df["order_id"].is_unique, "order_id must be unique after cleaning"
    assert df.isna().sum().sum() == 0, "no missing values should remain"
    assert (df["quantity"] > 0).all(), "quantity must be positive"
    assert df["discount"].between(0, 1).all(), "discount must be between 0 and 1"
    assert (df["shipping_days"] >= 0).all(), "ship date cannot be before order date"
    assert set(df["region"]) <= {"North", "South", "East", "West", "Central"}, "unexpected region label"


if __name__ == "__main__":
    raw = pd.read_csv(RAW)
    clean_df, report = clean(raw)
    validate(clean_df)
    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(CLEAN, index=False, date_format="%Y-%m-%d")

    print("Cleaning report")
    print(f"  Rows in:             {report['rows_in']:,}")
    print(f"  Duplicates removed:  {report['duplicates_removed']:,}")
    print(f"  Missing values before: {report['missing_before']}")
    print(f"  Missing values after:  {report['missing_after']}")
    print(f"  Rows out:            {report['rows_out']:,}")
    print(f"Saved clean data to {CLEAN}")
