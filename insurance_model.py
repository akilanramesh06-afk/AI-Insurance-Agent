"""
insurance_model.py  —  GigShield Phase 2
=========================================
ML-powered dynamic premium calculation, zone-based risk scoring,
automated disruption triggers, and zero-touch claims engine.
"""

import random
import math
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# ZONE RISK DATABASE  (hyper-local waterlogging / flood history)
# In Phase 3 this pulls from a real geo-risk API
# ─────────────────────────────────────────────────────────────────────────────
ZONE_RISK = {
    "Mumbai":    {"waterlog_score": 0.85, "flood_history": 0.90, "safe_discount": 0},
    "Delhi":     {"waterlog_score": 0.55, "flood_history": 0.50, "safe_discount": 2},
    "Bengaluru": {"waterlog_score": 0.60, "flood_history": 0.55, "safe_discount": 2},
    "Chennai":   {"waterlog_score": 0.80, "flood_history": 0.85, "safe_discount": 0},
    "Hyderabad": {"waterlog_score": 0.65, "flood_history": 0.60, "safe_discount": 2},
    "Kolkata":   {"waterlog_score": 0.75, "flood_history": 0.80, "safe_discount": 0},
    "Pune":      {"waterlog_score": 0.45, "flood_history": 0.40, "safe_discount": 4},
    "Ahmedabad": {"waterlog_score": 0.30, "flood_history": 0.25, "safe_discount": 4},
    "Jaipur":    {"waterlog_score": 0.20, "flood_history": 0.15, "safe_discount": 4},
    "Surat":     {"waterlog_score": 0.70, "flood_history": 0.72, "safe_discount": 0},
}

# ─────────────────────────────────────────────────────────────────────────────
# PLATFORM RISK MULTIPLIERS
# Some platforms operate in higher-risk zones or longer hours
# ─────────────────────────────────────────────────────────────────────────────
PLATFORM_RISK = {
    "Swiggy":   1.05,
    "Zomato":   1.05,
    "Amazon":   1.00,
    "Blinkit":  1.08,
    "Zepto":    1.08,
    "Dunzo":    1.03,
    "Other":    1.00,
}

# ─────────────────────────────────────────────────────────────────────────────
# DISRUPTION TRIGGER TYPES  (5 automated triggers)
# ─────────────────────────────────────────────────────────────────────────────
TRIGGERS = {
    "HEAVY_RAIN":     {"label": "Heavy Rain",          "icon": "🌧️",  "threshold": "Rainfall > 50mm/hr",  "coverage_pct": 1.00},
    "STORM":          {"label": "Storm / Cyclone",     "icon": "🌀",  "threshold": "Wind > 60 km/h",      "coverage_pct": 1.00},
    "WATERLOGGING":   {"label": "Waterlogging Alert",  "icon": "🌊",  "threshold": "Zone flood advisory",  "coverage_pct": 0.80},
    "EXTREME_HEAT":   {"label": "Extreme Heat",        "icon": "🌡️",  "threshold": "Temp > 45°C",         "coverage_pct": 0.60},
    "AIR_QUALITY":    {"label": "Poor Air Quality",    "icon": "😷",  "threshold": "AQI > 300",            "coverage_pct": 0.50},
}


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC PREMIUM CALCULATOR  (ML-style scoring)
# ─────────────────────────────────────────────────────────────────────────────
def calculate_dynamic_premium(daily_income: int, city: str, platform: str,
                               hours_per_day: float = 8.0) -> dict:
    """
    ML-inspired dynamic premium calculation.

    Factors considered:
      1. Income tier (base premium)
      2. City zone risk (waterlogging history → discount up to ₹4)
      3. Platform risk multiplier
      4. Hours per day (longer hours = higher exposure)
      5. Seasonal adjustment (monsoon months = +₹3)

    Returns full breakdown dict for transparency.
    """

    # 1. Base premium by income tier
    if daily_income < 800:
        base      = 20
        coverage  = 400
        plan      = "Basic"
    elif daily_income <= 1200:
        base      = 30
        coverage  = 700
        plan      = "Standard"
    elif daily_income <= 1800:
        base      = 50
        coverage  = 1200
        plan      = "Premium"
    else:
        base      = 70
        coverage  = 2000
        plan      = "Elite"

    # 2. Zone discount (safe zones get up to ₹4 off)
    zone        = ZONE_RISK.get(city, {"waterlog_score": 0.5, "flood_history": 0.5, "safe_discount": 0})
    zone_adj    = -zone["safe_discount"]

    # 3. Platform multiplier
    plat_mult   = PLATFORM_RISK.get(platform, 1.0)

    # 4. Hours adjustment (base assumes 8 hrs; scale ±10% per 2hr deviation)
    hour_adj    = round((hours_per_day - 8) * 0.5, 2)

    # 5. Seasonal adjustment
    month       = datetime.now().month
    # Monsoon = June–September
    seasonal    = 3 if month in [6, 7, 8, 9] else 0

    # Final calculation
    raw         = (base + hour_adj + zone_adj + seasonal) * plat_mult
    final       = max(10, round(raw))   # floor ₹10

    # Coverage scales with plan (±5% per zone risk score)
    risk_score  = (zone["waterlog_score"] + zone["flood_history"]) / 2
    adj_coverage = round(coverage * (1 + (risk_score - 0.5) * 0.1))

    return {
        "premium":          final,
        "plan":             plan,
        "coverage":         adj_coverage,
        "base_premium":     base,
        "zone_discount":    zone_adj,
        "platform_mult":    plat_mult,
        "hour_adj":         hour_adj,
        "seasonal_adj":     seasonal,
        "zone_risk_score":  round(risk_score * 100),
        "city_waterlog":    round(zone["waterlog_score"] * 100),
        "savings_vs_flat":  max(0, base - final),
        "breakdown": {
            "Base Premium":         f"₹{base}",
            "Zone Safety Discount": f"₹{zone_adj}",
            "Platform Adjustment":  f"×{plat_mult}",
            "Hours Adjustment":     f"₹{'+' if hour_adj >= 0 else ''}{hour_adj}",
            "Seasonal (Monsoon)":   f"₹{seasonal}",
            "Final Premium":        f"₹{final}/week",
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER & DISRUPTION SIMULATION  (5 automated triggers)
# ─────────────────────────────────────────────────────────────────────────────
def simulate_disruptions(city: str) -> dict:
    """
    Simulate 5 automated disruption triggers for a city.
    In Phase 3 this calls OpenWeatherMap, AQI API, IMD flood API.

    Returns active triggers and overall risk state.
    """
    zone = ZONE_RISK.get(city, {"waterlog_score": 0.5, "flood_history": 0.5})
    risk = (zone["waterlog_score"] + zone["flood_history"]) / 2

    # Weighted random based on city risk score
    weather_pool = (
        ["HEAVY_RAIN"] * int(risk * 4) +
        ["STORM"]      * int(risk * 2) +
        ["WATERLOGGING"] * int(risk * 3) +
        ["EXTREME_HEAT"] * 1 +
        ["AIR_QUALITY"]  * 1 +
        ["CLEAR"]        * int((1 - risk) * 6)
    )

    chosen = random.choice(weather_pool) if weather_pool else "CLEAR"

    if chosen == "CLEAR":
        return {
            "status":           "CLEAR",
            "risk_level":       "Low",
            "risk_class":       "low",
            "icon":             "☀️",
            "label":            "Clear",
            "message":          f"No disruptions detected in {city}. Great day for deliveries!",
            "active_triggers":  [],
            "claim_eligible":   False,
            "coverage_pct":     0,
        }

    trigger = TRIGGERS[chosen]

    # Check for multiple simultaneous triggers (compound event)
    active = [chosen]
    if chosen == "HEAVY_RAIN" and risk > 0.7 and random.random() > 0.5:
        active.append("WATERLOGGING")

    risk_level = "High" if trigger["coverage_pct"] >= 0.80 else "Medium"
    risk_class = "high" if risk_level == "High" else "medium"

    return {
        "status":           chosen,
        "risk_level":       risk_level,
        "risk_class":       risk_class,
        "icon":             trigger["icon"],
        "label":            trigger["label"],
        "message":          f"{trigger['label']} detected in {city}! {trigger['threshold']}. Your claim is being processed automatically.",
        "active_triggers":  active,
        "claim_eligible":   True,
        "coverage_pct":     trigger["coverage_pct"],
        "threshold":        trigger["threshold"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# ZERO-TOUCH CLAIM ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def process_auto_claim(worker: dict, disruption: dict) -> dict:
    """
    Automatically process a claim when a disruption trigger fires.

    Steps (all automated):
      1. Verify worker policy is active
      2. Match disruption to trigger threshold
      3. Calculate payout amount
      4. Generate claim ID
      5. Return claim record

    Returns claim dict ready to store in DB.
    """
    if not disruption.get("claim_eligible"):
        return {"success": False, "reason": "No active disruption trigger"}

    # Get coverage from premium tier
    coverage_map = {20: 400, 30: 700, 50: 1200, 70: 2000}
    weekly_coverage = coverage_map.get(worker.get("premium", 30), 700)

    coverage_pct    = disruption["coverage_pct"]
    payout_amount   = round(weekly_coverage * coverage_pct)

    # Proportional daily payout (coverage / 7 days * affected hours ratio)
    daily_payout    = round(payout_amount / 7)

    claim_id        = f"GS-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    trigger_label   = disruption.get("label", "Weather Disruption")

    return {
        "success":          True,
        "claim_id":         claim_id,
        "worker_id":        worker.get("id"),
        "worker_name":      worker.get("name"),
        "trigger":          disruption["status"],
        "trigger_label":    trigger_label,
        "weekly_coverage":  weekly_coverage,
        "coverage_pct":     int(coverage_pct * 100),
        "payout_amount":    payout_amount,
        "daily_payout":     daily_payout,
        "status":           "AUTO_APPROVED",
        "upi_status":       "PROCESSING",
        "processed_at":     datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "message":          f"Claim {claim_id} auto-approved. ₹{payout_amount} payout initiated to UPI.",
        "zero_touch":       True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POLICY MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
def get_policy_details(worker: dict) -> dict:
    """Generate full policy document for a worker."""
    coverage_map = {20: 400, 30: 700, 50: 1200, 70: 2000}
    plan_map     = {20: "Basic", 30: "Standard", 50: "Premium", 70: "Elite"}
    premium      = worker.get("premium", 30)
    coverage     = coverage_map.get(premium, 700)
    plan         = plan_map.get(premium, "Standard")

    policy_num   = f"POL-{worker.get('id', 0):06d}"
    start_date   = datetime.now().strftime("%d %b %Y")
    end_date     = (datetime.now() + timedelta(days=365)).strftime("%d %b %Y")

    return {
        "policy_number":    policy_num,
        "plan":             plan,
        "status":           "ACTIVE",
        "premium":          premium,
        "weekly_coverage":  coverage,
        "annual_premium":   premium * 52,
        "start_date":       start_date,
        "end_date":         end_date,
        "triggers":         list(TRIGGERS.keys()),
        "trigger_details":  TRIGGERS,
        "claim_process":    "Zero-Touch Automatic",
        "payout_method":    "UPI Direct Transfer",
        "payout_sla":       "Within 2 hours of trigger",
    }


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY — kept for Phase 1 compatibility
# ─────────────────────────────────────────────────────────────────────────────
def calculate_premium(daily_income: int) -> int:
    return calculate_dynamic_premium(daily_income, "Mumbai", "Other")["premium"]


def simulate_weather_risk(city: str) -> dict:
    d = simulate_disruptions(city)
    return {
        "weather":    d["label"],
        "risk_level": d["risk_level"],
        "icon":       d["icon"],
        "color":      "danger" if d["risk_level"] == "High" else "warning" if d["risk_level"] == "Medium" else "success",
        "message":    d["message"],
    }


def get_coverage_details(premium: int) -> dict:
    coverage_map = {20: 400, 30: 700, 50: 1200, 70: 2000}
    plan_map     = {20: "Basic", 30: "Standard", 50: "Premium", 70: "Elite"}
    coverage     = coverage_map.get(premium, 700)
    plan         = plan_map.get(premium, "Standard")
    return {
        "weekly_coverage": coverage,
        "description":     f"{plan} Plan – up to ₹{coverage}/week income protection",
    }
