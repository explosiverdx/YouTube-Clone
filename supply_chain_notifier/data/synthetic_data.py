"""Generate synthetic supply chain data with embedded disruption scenarios."""

import csv
import io
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

PRODUCT_LINES = [
    "Organic Cereal", "Sports Drink", "Baby Formula", "Frozen Pizza",
    "Laundry Detergent", "Shampoo", "Canned Soup", "Snack Bars",
    "Pet Food", "Bottled Water",
]

SUPPLIERS = [
    {"id": "SUP-001", "name": "AgriSource Inc.", "region": "Midwest US", "reliability": 0.92},
    {"id": "SUP-002", "name": "PackRight Ltd.", "region": "Southeast Asia", "reliability": 0.85},
    {"id": "SUP-003", "name": "ChemBlend Corp.", "region": "Western Europe", "reliability": 0.95},
    {"id": "SUP-004", "name": "FreshHarvest Co.", "region": "South America", "reliability": 0.78},
    {"id": "SUP-005", "name": "MetalWorks Global", "region": "East Asia", "reliability": 0.88},
]

WAREHOUSES = ["WH-Chicago", "WH-Dallas", "WH-Newark", "WH-LA", "WH-Atlanta"]

DISRUPTION_SCENARIOS = [
    {"type": "raw_material_shortage", "label": "Raw Material Shortage",
     "affects": "inventory", "severity": "CRITICAL"},
    {"type": "transport_delay", "label": "Transportation Delay",
     "affects": "shipment", "severity": "HIGH"},
    {"type": "supplier_issue", "label": "Supplier Reliability Drop",
     "affects": "supplier", "severity": "HIGH"},
    {"type": "demand_spike", "label": "Unexpected Demand Spike",
     "affects": "inventory", "severity": "MEDIUM"},
    {"type": "quality_defect", "label": "Quality Control Failure",
     "affects": "quality", "severity": "CRITICAL"},
    {"type": "port_congestion", "label": "Port Congestion",
     "affects": "shipment", "severity": "MEDIUM"},
]


def generate_shipment_data(n_records: int = 200, disruption_pct: float = 0.15) -> pd.DataFrame:
    rows = []
    base_date = datetime.now() - timedelta(days=30)

    for i in range(n_records):
        product = random.choice(PRODUCT_LINES)
        supplier = random.choice(SUPPLIERS)
        warehouse = random.choice(WAREHOUSES)
        ship_date = base_date + timedelta(days=random.randint(0, 30))
        expected_days = random.randint(2, 10)
        is_disrupted = random.random() < disruption_pct

        if is_disrupted:
            actual_days = expected_days + random.randint(3, 15)
            status = random.choice(["DELAYED", "STUCK_IN_TRANSIT", "REROUTED"])
            disruption = random.choice(["transport_delay", "port_congestion"])
        else:
            actual_days = expected_days + random.randint(-1, 1)
            status = "DELIVERED" if random.random() > 0.1 else "IN_TRANSIT"
            disruption = "none"

        rows.append({
            "shipment_id": f"SHP-{i+1:04d}",
            "product": product,
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "origin_region": supplier["region"],
            "destination_warehouse": warehouse,
            "ship_date": ship_date.strftime("%Y-%m-%d"),
            "expected_delivery_days": expected_days,
            "actual_delivery_days": max(actual_days, 0),
            "delay_days": max(actual_days - expected_days, 0),
            "quantity": random.randint(100, 5000),
            "status": status,
            "disruption_type": disruption,
        })

    return pd.DataFrame(rows)


def generate_inventory_data(n_records: int = 150, disruption_pct: float = 0.2) -> pd.DataFrame:
    rows = []
    base_date = datetime.now() - timedelta(days=30)

    for i in range(n_records):
        product = random.choice(PRODUCT_LINES)
        warehouse = random.choice(WAREHOUSES)
        record_date = base_date + timedelta(days=random.randint(0, 30))
        is_disrupted = random.random() < disruption_pct
        normal_level = random.randint(200, 2000)
        reorder_point = int(normal_level * 0.3)

        if is_disrupted:
            scenario = random.choice(["raw_material_shortage", "demand_spike"])
            if scenario == "raw_material_shortage":
                current_level = random.randint(5, 40)
                daily_demand = random.randint(30, 80)
            else:
                current_level = random.randint(50, 150)
                daily_demand = random.randint(80, 200)
            disruption = scenario
        else:
            current_level = random.randint(reorder_point, normal_level)
            daily_demand = random.randint(20, 60)
            disruption = "none"

        days_of_supply = round(current_level / max(daily_demand, 1), 1)

        rows.append({
            "record_id": f"INV-{i+1:04d}",
            "product": product,
            "warehouse": warehouse,
            "date": record_date.strftime("%Y-%m-%d"),
            "current_stock_level": current_level,
            "normal_stock_level": normal_level,
            "reorder_point": reorder_point,
            "daily_demand": daily_demand,
            "days_of_supply": days_of_supply,
            "stock_status": "CRITICAL" if current_level < 50 else "LOW" if current_level < reorder_point else "NORMAL",
            "disruption_type": disruption,
        })

    return pd.DataFrame(rows)


def generate_supplier_data(n_records: int = 100, disruption_pct: float = 0.15) -> pd.DataFrame:
    rows = []
    base_date = datetime.now() - timedelta(days=30)

    for i in range(n_records):
        supplier = random.choice(SUPPLIERS)
        record_date = base_date + timedelta(days=random.randint(0, 30))
        is_disrupted = random.random() < disruption_pct

        if is_disrupted:
            on_time_rate = round(random.uniform(0.3, 0.65), 2)
            quality_score = round(random.uniform(0.5, 0.75), 2)
            defect_rate = round(random.uniform(0.06, 0.15), 3)
            disruption = random.choice(["supplier_issue", "quality_defect"])
        else:
            on_time_rate = round(random.uniform(0.8, 0.99), 2)
            quality_score = round(random.uniform(0.85, 0.99), 2)
            defect_rate = round(random.uniform(0.001, 0.04), 3)
            disruption = "none"

        rows.append({
            "report_id": f"SPR-{i+1:04d}",
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "region": supplier["region"],
            "date": record_date.strftime("%Y-%m-%d"),
            "on_time_delivery_rate": on_time_rate,
            "quality_score": quality_score,
            "defect_rate": defect_rate,
            "orders_fulfilled": random.randint(10, 100),
            "orders_delayed": random.randint(0, 20) if is_disrupted else random.randint(0, 3),
            "baseline_reliability": supplier["reliability"],
            "disruption_type": disruption,
        })

    return pd.DataFrame(rows)


def generate_all_sample_data(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

    shipments = generate_shipment_data()
    inventory = generate_inventory_data()
    suppliers = generate_supplier_data()

    return shipments, inventory, suppliers


def save_sample_csv(output_dir: str = "data"):
    import os
    os.makedirs(output_dir, exist_ok=True)

    shipments, inventory, suppliers = generate_all_sample_data()
    shipments.to_csv(f"{output_dir}/shipments.csv", index=False)
    inventory.to_csv(f"{output_dir}/inventory.csv", index=False)
    suppliers.to_csv(f"{output_dir}/suppliers.csv", index=False)

    return {
        "shipments": len(shipments),
        "inventory": len(inventory),
        "suppliers": len(suppliers),
    }


if __name__ == "__main__":
    counts = save_sample_csv()
    print(f"Generated sample data: {counts}")
