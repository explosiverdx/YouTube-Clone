"""Data preprocessing: normalization, tagging, and feature engineering."""

import io

import numpy as np
import pandas as pd


def normalize_column(series: pd.Series) -> pd.Series:
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return pd.Series(0.0, index=series.index)
    return (series - min_val) / (max_val - min_val)


def preprocess_shipment_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")
    df["delay_days"] = pd.to_numeric(df["delay_days"], errors="coerce").fillna(0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)

    df["delay_norm"] = normalize_column(df["delay_days"])
    df["is_severely_delayed"] = (df["delay_days"] >= 3).astype(int)

    df["event_tag"] = df.apply(
        lambda r: "SEVERE_DELAY" if r["delay_days"] >= 7
        else "MODERATE_DELAY" if r["delay_days"] >= 3
        else "ON_TIME", axis=1
    )
    return df


def preprocess_inventory_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["current_stock_level"] = pd.to_numeric(df["current_stock_level"], errors="coerce").fillna(0)
    df["daily_demand"] = pd.to_numeric(df["daily_demand"], errors="coerce").fillna(1)
    df["days_of_supply"] = pd.to_numeric(df["days_of_supply"], errors="coerce").fillna(0)

    df["stock_ratio"] = df["current_stock_level"] / df["normal_stock_level"].replace(0, 1)
    df["stock_ratio_norm"] = normalize_column(df["stock_ratio"])

    df["event_tag"] = df.apply(
        lambda r: "STOCKOUT_IMMINENT" if r["days_of_supply"] < 1
        else "CRITICAL_LOW" if r["current_stock_level"] < 50
        else "LOW_STOCK" if r["stock_status"] == "LOW"
        else "NORMAL", axis=1
    )
    return df


def preprocess_supplier_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["on_time_delivery_rate"] = pd.to_numeric(df["on_time_delivery_rate"], errors="coerce").fillna(0)
    df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce").fillna(0)
    df["defect_rate"] = pd.to_numeric(df["defect_rate"], errors="coerce").fillna(0)

    df["reliability_drop"] = df["baseline_reliability"] - df["on_time_delivery_rate"]
    df["reliability_drop_norm"] = normalize_column(df["reliability_drop"].clip(lower=0))

    df["event_tag"] = df.apply(
        lambda r: "QUALITY_FAILURE" if r["defect_rate"] > 0.05
        else "RELIABILITY_DROP" if r["on_time_delivery_rate"] < 0.7
        else "WATCH" if r["on_time_delivery_rate"] < 0.85
        else "NORMAL", axis=1
    )
    return df


def auto_detect_and_preprocess(file_content: bytes, filename: str) -> tuple[pd.DataFrame, str]:
    """Auto-detect file type (CSV/JSON) and data category, then preprocess."""
    if filename.endswith(".json"):
        df = pd.read_json(io.BytesIO(file_content))
    else:
        df = pd.read_csv(io.BytesIO(file_content))

    cols_lower = [c.lower() for c in df.columns]

    if any("shipment" in c or "delay" in c or "ship_date" in c for c in cols_lower):
        return preprocess_shipment_data(df), "shipment"
    elif any("stock" in c or "inventory" in c or "days_of_supply" in c for c in cols_lower):
        return preprocess_inventory_data(df), "inventory"
    elif any("supplier" in c or "defect" in c or "reliability" in c for c in cols_lower):
        return preprocess_supplier_data(df), "supplier"
    else:
        return df, "unknown"
