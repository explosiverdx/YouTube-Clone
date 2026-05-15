"""AI Agent for detecting supply chain disruptions using rule-based + ML anomaly detection."""

from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import DISRUPTION_THRESHOLDS


def _run_isolation_forest(features: np.ndarray, contamination: float = 0.15) -> np.ndarray:
    if len(features) < 10:
        return np.ones(len(features))
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    predictions = model.fit_predict(scaled)
    return predictions  # -1 = anomaly, 1 = normal


def detect_shipment_disruptions(df: pd.DataFrame) -> list[dict]:
    alerts = []
    thresholds = DISRUPTION_THRESHOLDS

    features = df[["delay_days", "quantity"]].values
    anomaly_labels = _run_isolation_forest(features)

    for idx, row in df.iterrows():
        is_anomaly = anomaly_labels[idx] == -1
        delay = row.get("delay_days", 0)

        if delay >= 7 or (is_anomaly and delay >= 3):
            severity = "CRITICAL" if delay >= 10 else "HIGH" if delay >= 5 else "MEDIUM"
            alerts.append({
                "id": f"ALERT-SHP-{row.get('shipment_id', idx)}",
                "timestamp": datetime.now().isoformat(),
                "category": "Shipment",
                "type": "Transportation Delay",
                "severity": severity,
                "product": row.get("product", "Unknown"),
                "details": {
                    "shipment_id": row.get("shipment_id", ""),
                    "supplier": row.get("supplier_name", ""),
                    "origin": row.get("origin_region", ""),
                    "destination": row.get("destination_warehouse", ""),
                    "delay_days": int(delay),
                    "status": row.get("status", ""),
                    "ml_anomaly": bool(is_anomaly),
                },
                "message": (
                    f"Shipment {row.get('shipment_id', '')} of {row.get('product', '')} "
                    f"from {row.get('supplier_name', '')} is delayed by {int(delay)} days. "
                    f"Status: {row.get('status', '')}. Destination: {row.get('destination_warehouse', '')}."
                ),
            })

    return alerts


def detect_inventory_disruptions(df: pd.DataFrame) -> list[dict]:
    alerts = []
    thresholds = DISRUPTION_THRESHOLDS

    features = df[["current_stock_level", "daily_demand", "days_of_supply"]].values
    anomaly_labels = _run_isolation_forest(features)

    for idx, row in df.iterrows():
        is_anomaly = anomaly_labels[idx] == -1
        stock = row.get("current_stock_level", 0)
        dos = row.get("days_of_supply", 999)

        if stock < thresholds["inventory_critical_low"] or dos < 1 or is_anomaly:
            if stock < 20 or dos < 0.5:
                severity = "CRITICAL"
            elif stock < thresholds["inventory_critical_low"]:
                severity = "HIGH"
            elif is_anomaly:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            disruption_type = "Demand Spike" if row.get("daily_demand", 0) > 80 else "Stock Shortage"

            alerts.append({
                "id": f"ALERT-INV-{row.get('record_id', idx)}",
                "timestamp": datetime.now().isoformat(),
                "category": "Inventory",
                "type": disruption_type,
                "severity": severity,
                "product": row.get("product", "Unknown"),
                "details": {
                    "record_id": row.get("record_id", ""),
                    "warehouse": row.get("warehouse", ""),
                    "current_stock": int(stock),
                    "normal_stock": int(row.get("normal_stock_level", 0)),
                    "daily_demand": int(row.get("daily_demand", 0)),
                    "days_of_supply": float(dos),
                    "ml_anomaly": bool(is_anomaly),
                },
                "message": (
                    f"{row.get('product', '')} at {row.get('warehouse', '')} — "
                    f"stock critically low at {int(stock)} units "
                    f"({dos} days of supply remaining). "
                    f"Daily demand: {int(row.get('daily_demand', 0))} units."
                ),
            })

    return alerts


def detect_supplier_disruptions(df: pd.DataFrame) -> list[dict]:
    alerts = []
    thresholds = DISRUPTION_THRESHOLDS

    features = df[["on_time_delivery_rate", "quality_score", "defect_rate"]].values
    anomaly_labels = _run_isolation_forest(features)

    for idx, row in df.iterrows():
        is_anomaly = anomaly_labels[idx] == -1
        otr = row.get("on_time_delivery_rate", 1.0)
        defect = row.get("defect_rate", 0)
        quality = row.get("quality_score", 1.0)

        triggered = (
            otr < thresholds["supplier_reliability_min"]
            or defect > thresholds["quality_defect_rate_max"]
            or is_anomaly
        )

        if triggered:
            if defect > 0.1 or quality < 0.6:
                severity = "CRITICAL"
            elif otr < 0.6 or defect > thresholds["quality_defect_rate_max"]:
                severity = "HIGH"
            elif is_anomaly:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            disruption_type = "Quality Defect" if defect > thresholds["quality_defect_rate_max"] else "Supplier Reliability Drop"

            alerts.append({
                "id": f"ALERT-SUP-{row.get('report_id', idx)}",
                "timestamp": datetime.now().isoformat(),
                "category": "Supplier",
                "type": disruption_type,
                "severity": severity,
                "product": f"Supplier: {row.get('supplier_name', '')}",
                "details": {
                    "report_id": row.get("report_id", ""),
                    "supplier_id": row.get("supplier_id", ""),
                    "supplier_name": row.get("supplier_name", ""),
                    "region": row.get("region", ""),
                    "on_time_rate": float(otr),
                    "quality_score": float(quality),
                    "defect_rate": float(defect),
                    "orders_delayed": int(row.get("orders_delayed", 0)),
                    "ml_anomaly": bool(is_anomaly),
                },
                "message": (
                    f"Supplier {row.get('supplier_name', '')} ({row.get('region', '')}) — "
                    f"on-time delivery: {otr:.0%}, quality: {quality:.0%}, "
                    f"defect rate: {defect:.1%}. "
                    f"{int(row.get('orders_delayed', 0))} orders delayed."
                ),
            })

    return alerts


def run_full_detection(shipment_df=None, inventory_df=None, supplier_df=None) -> list[dict]:
    all_alerts = []

    if shipment_df is not None and not shipment_df.empty:
        all_alerts.extend(detect_shipment_disruptions(shipment_df))
    if inventory_df is not None and not inventory_df.empty:
        all_alerts.extend(detect_inventory_disruptions(inventory_df))
    if supplier_df is not None and not supplier_df.empty:
        all_alerts.extend(detect_supplier_disruptions(supplier_df))

    all_alerts.sort(key=lambda a: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(a["severity"], 4))

    return all_alerts
