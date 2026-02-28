"""
Data loading and KPI calculations for the Private Business Intelligence Agent.
Handles reading the Excel dataset and computing derived columns.
"""

import streamlit as st
import pandas as pd


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """
    Read the Excel dataset and compute derived KPI columns.

    Columns added:
        SALES       = SELLING_PRICE_PER_UNIT × UNITS_SOLD
        COGS        = COST_PER_UNIT × UNITS_SOLD
        MARGIN      = SALES − COGS
        MARGIN_RATE = MARGIN / SALES   (0‒1 scale)

    Returns the full DataFrame with KPI columns appended.
    """
    df = pd.read_excel(path)

    # Derived KPIs
    df["SALES"] = df["SELLING_PRICE_PER_UNIT"] * df["UNITS_SOLD"]
    df["COGS"] = df["COST_PER_UNIT"] * df["UNITS_SOLD"]
    df["MARGIN"] = df["SALES"] - df["COGS"]
    # Avoid division by zero - fill with 0 where SALES == 0
    df["MARGIN_RATE"] = (df["MARGIN"] / df["SALES"]).fillna(0)

    return df


def get_dataset_summary(df: pd.DataFrame) -> dict:
    """
    Build a summary dict used to populate the sidebar stats
    and to give the LLM context about the dataset.

    Returns dict with keys:
        total_rows, years, regions, divisions, categories, brands,
        sales_by_year  (dict {year: total_sales})
    """
    sales_by_year = (
        df.groupby("YEAR")["SALES"]
        .sum()
        .to_dict()
    )

    summary = {
        "total_rows": len(df),
        "years": sorted(df["YEAR"].unique().tolist()),
        "regions": sorted(df["REGION"].unique().tolist()),
        "divisions": sorted(df["PRODUCT_DIVISION"].unique().tolist()),
        "categories": sorted(df["PRODUCT_CATEGORY"].unique().tolist()),
        "brands": sorted(df["BRAND"].unique().tolist()),
        "store_names": sorted(df["STORE_NAME"].unique().tolist()) if "STORE_NAME" in df.columns else [],
        "sales_by_year": sales_by_year,
    }
    return summary
