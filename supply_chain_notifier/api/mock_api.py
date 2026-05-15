"""Mock Supply Chain Status API — simulates a live data feed."""

import random
from datetime import datetime, timedelta

from flask import Blueprint, jsonify

mock_api = Blueprint("mock_api", __name__)

_STATUS_POOL = [
    {"shipment_id": "LIVE-001", "product": "Organic Cereal", "status": "IN_TRANSIT",
     "origin": "Midwest US", "destination": "WH-Chicago", "eta_days": 2},
    {"shipment_id": "LIVE-002", "product": "Sports Drink", "status": "DELAYED",
     "origin": "Southeast Asia", "destination": "WH-LA", "eta_days": 8},
    {"shipment_id": "LIVE-003", "product": "Baby Formula", "status": "DELIVERED",
     "origin": "Western Europe", "destination": "WH-Newark", "eta_days": 0},
    {"shipment_id": "LIVE-004", "product": "Frozen Pizza", "status": "STUCK_IN_TRANSIT",
     "origin": "South America", "destination": "WH-Dallas", "eta_days": 12},
    {"shipment_id": "LIVE-005", "product": "Laundry Detergent", "status": "IN_TRANSIT",
     "origin": "East Asia", "destination": "WH-Atlanta", "eta_days": 3},
]


@mock_api.route("/api/v1/status", methods=["GET"])
def get_live_status():
    statuses = []
    for item in _STATUS_POOL:
        entry = item.copy()
        entry["checked_at"] = datetime.now().isoformat()
        if entry["status"] in ("DELAYED", "STUCK_IN_TRANSIT"):
            entry["delay_days"] = random.randint(3, 15)
            entry["risk_flag"] = True
        else:
            entry["delay_days"] = 0
            entry["risk_flag"] = False
        statuses.append(entry)
    return jsonify({"source": "Mock Supply Chain API", "timestamp": datetime.now().isoformat(), "data": statuses})


@mock_api.route("/api/v1/inventory", methods=["GET"])
def get_live_inventory():
    products = ["Organic Cereal", "Sports Drink", "Baby Formula", "Frozen Pizza", "Snack Bars"]
    warehouses = ["WH-Chicago", "WH-Dallas", "WH-Newark", "WH-LA", "WH-Atlanta"]
    data = []
    for product in products:
        wh = random.choice(warehouses)
        stock = random.randint(10, 1500)
        demand = random.randint(20, 120)
        data.append({
            "product": product,
            "warehouse": wh,
            "current_stock": stock,
            "daily_demand": demand,
            "days_of_supply": round(stock / max(demand, 1), 1),
            "status": "CRITICAL" if stock < 50 else "LOW" if stock < 200 else "NORMAL",
        })
    return jsonify({"source": "Mock Inventory API", "timestamp": datetime.now().isoformat(), "data": data})


@mock_api.route("/api/v1/suppliers", methods=["GET"])
def get_live_suppliers():
    from data.synthetic_data import SUPPLIERS
    data = []
    for s in SUPPLIERS:
        otr = round(random.uniform(0.5, 0.99), 2)
        data.append({
            "supplier_id": s["id"],
            "name": s["name"],
            "region": s["region"],
            "on_time_rate": otr,
            "quality_score": round(random.uniform(0.6, 0.99), 2),
            "status": "AT_RISK" if otr < 0.7 else "WATCH" if otr < 0.85 else "HEALTHY",
        })
    return jsonify({"source": "Mock Supplier API", "timestamp": datetime.now().isoformat(), "data": data})
