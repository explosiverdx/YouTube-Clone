import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_GENAI = bool(GEMINI_API_KEY)
SECRET_KEY = os.getenv("SECRET_KEY", "supply-chain-secret-key-2026")

DISRUPTION_THRESHOLDS = {
    "inventory_critical_low": 50,
    "delivery_delay_days": 3,
    "supplier_reliability_min": 0.7,
    "demand_spike_multiplier": 1.5,
    "quality_defect_rate_max": 0.05,
}

SEVERITY_LEVELS = {
    "CRITICAL": {"color": "#dc3545", "priority": 1},
    "HIGH": {"color": "#fd7e14", "priority": 2},
    "MEDIUM": {"color": "#ffc107", "priority": 3},
    "LOW": {"color": "#28a745", "priority": 4},
}
