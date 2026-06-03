"""
app.py — GigShield Phase 2
===========================
AI-Powered Parametric Insurance Platform for India's Gig Workers.

API Routes:
  POST /api/register          → Register worker + calculate dynamic premium
  GET  /api/dashboard/<id>    → Worker dashboard data
  POST /api/simulate-risk/<id>→ Simulate disruptions & trigger claim
  GET  /api/claims/<id>       → Worker's claim history
  GET  /api/admin/stats        → Admin aggregate stats
  GET  /api/admin/workers      → All workers list
  DELETE /api/admin/workers/<id> → Delete worker
  GET  /api/fraud-check/<id>  → Fraud analytics for worker
  GET  /api/leaderboard       → Top cities by risk score
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import random, math, hashlib

from insurance_model import (
    calculate_dynamic_premium,
    simulate_disruptions,
    process_auto_claim,
    get_policy_details,
    ZONE_RISK,
    PLATFORM_RISK,
    TRIGGERS,
)

# ─── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Allow single-page HTML to call the API
app.secret_key = "gigshield_phase2_secret"


# ─── DB helper ───────────────────────────────────────────────────────────────
def get_db():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Mysql@1234",      # ← update if needed
            database="gig_insurance",
        )
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


def db_query(sql, params=(), fetch="all", commit=False):
    """Utility: run a query and return results or lastrowid."""
    conn = get_db()
    if conn is None:
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        if fetch == "one":
            return cur.fetchone()
        return cur.fetchall()
    except Error as e:
        print(f"[QUERY ERROR] {e}")
        return None
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# FRAUD DETECTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def fraud_analysis(worker_id: int) -> dict:
    """
    Anomaly detection on claim behaviour for a worker.
    Checks:
      1. Claim frequency (>3 claims/week = suspicious)
      2. Duplicate triggers on same day
      3. Coverage-to-premium ratio outlier
      4. Location mismatch (simulated)
    """
    claims = db_query(
        "SELECT * FROM claims WHERE worker_id = %s ORDER BY processed_at DESC LIMIT 20",
        (worker_id,)
    ) or []

    flags = []
    score = 100  # Start clean

    # 1. Frequency check
    week_ago = datetime.now() - timedelta(days=7)
    recent = [c for c in claims if c["processed_at"] >= week_ago]
    if len(recent) > 3:
        flags.append({"type": "HIGH_FREQUENCY", "msg": f"{len(recent)} claims in 7 days (threshold: 3)", "severity": "high"})
        score -= 30

    # 2. Duplicate trigger check
    trigger_days = {}
    for c in claims:
        key = f"{c['trigger_type']}_{c['processed_at'].strftime('%Y-%m-%d')}"
        trigger_days[key] = trigger_days.get(key, 0) + 1
    dupes = {k: v for k, v in trigger_days.items() if v > 1}
    if dupes:
        flags.append({"type": "DUPLICATE_TRIGGER", "msg": f"Duplicate triggers detected on same day", "severity": "medium"})
        score -= 20

    # 3. Payout ratio
    worker = db_query("SELECT * FROM workers WHERE id = %s", (worker_id,), fetch="one")
    if worker and claims:
        total_payout = sum(c["payout_amount"] for c in claims)
        annual_premium = worker["premium"] * 52
        ratio = total_payout / max(annual_premium, 1)
        if ratio > 10:
            flags.append({"type": "HIGH_PAYOUT_RATIO", "msg": f"Payout/premium ratio {ratio:.1f}x (threshold: 10x)", "severity": "medium"})
            score -= 15

    # 4. Simulated location check
    if random.random() < 0.05:  # 5% chance of location anomaly
        flags.append({"type": "LOCATION_MISMATCH", "msg": "Claim location doesn't match registered city", "severity": "high"})
        score -= 25

    risk_label = "Low" if score >= 80 else "Medium" if score >= 60 else "High"
    return {
        "fraud_score":   max(0, score),
        "risk_label":    risk_label,
        "flags":         flags,
        "total_claims":  len(claims),
        "recent_claims": len(recent),
        "is_flagged":    score < 60,
    }


# ─────────────────────────────────────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    name          = str(data.get("name", "")).strip()
    city          = str(data.get("city", "")).strip()
    platform      = str(data.get("platform", "")).strip()
    daily_income  = int(data.get("daily_income", 0))
    hours_per_day = float(data.get("hours_per_day", 8.0))

    if not all([name, city, platform]) or daily_income <= 0:
        return jsonify({"error": "All fields are required and daily income must be positive."}), 400

    premium_data = calculate_dynamic_premium(daily_income, city, platform, hours_per_day)
    premium      = premium_data["premium"]

    wid = db_query(
        "INSERT INTO workers (name, city, platform, daily_income, premium, hours_per_day) VALUES (%s,%s,%s,%s,%s,%s)",
        (name, city, platform, daily_income, premium, hours_per_day),
        commit=True,
    )
    if wid is None:
        return jsonify({"error": "Database error. Please try again."}), 500

    policy = get_policy_details({"id": wid, "premium": premium})

    return jsonify({
        "worker_id":    wid,
        "premium_data": premium_data,
        "policy":       policy,
        "message":      f"Welcome, {name}! Your GigShield policy is active.",
    }), 201


@app.route("/api/dashboard/<int:worker_id>")
def api_dashboard(worker_id):
    worker = db_query("SELECT * FROM workers WHERE id = %s", (worker_id,), fetch="one")
    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    # Convert datetime to string for JSON
    worker["registered_at"] = worker["registered_at"].strftime("%d %b %Y, %I:%M %p")

    disruption   = simulate_disruptions(worker["city"])
    premium_data = calculate_dynamic_premium(
        worker["daily_income"], worker["city"], worker["platform"], worker.get("hours_per_day", 8.0)
    )
    policy       = get_policy_details(worker)
    claims       = db_query(
        "SELECT * FROM claims WHERE worker_id=%s ORDER BY processed_at DESC LIMIT 10",
        (worker_id,)
    ) or []
    for c in claims:
        c["processed_at"] = c["processed_at"].strftime("%d %b %Y, %I:%M %p")

    fraud        = fraud_analysis(worker_id)

    # Stats
    total_payout  = sum(c["payout_amount"] for c in claims)
    active_months = max(1, (datetime.now() - datetime.strptime(worker["registered_at"], "%d %b %Y, %I:%M %p")).days // 30)

    return jsonify({
        "worker":       worker,
        "disruption":   disruption,
        "premium_data": premium_data,
        "policy":       policy,
        "claims":       claims,
        "fraud":        fraud,
        "stats": {
            "total_claims":  len(claims),
            "total_payout":  total_payout,
            "active_months": active_months,
            "savings":       premium_data.get("savings_vs_flat", 0),
        },
    })


@app.route("/api/simulate-risk/<int:worker_id>", methods=["POST"])
def api_simulate_risk(worker_id):
    """Simulate a weather event and auto-process claim if triggered."""
    worker = db_query("SELECT * FROM workers WHERE id = %s", (worker_id,), fetch="one")
    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    disruption = simulate_disruptions(worker["city"])

    claim_result = None
    if disruption.get("claim_eligible"):
        claim_result = process_auto_claim(worker, disruption)
        if claim_result.get("success"):
            db_query(
                """INSERT INTO claims
                   (worker_id, claim_id, trigger_type, trigger_label, payout_amount, coverage_pct)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (
                    worker_id,
                    claim_result["claim_id"],
                    disruption["status"],
                    disruption["label"],
                    claim_result["payout_amount"],
                    int(disruption["coverage_pct"] * 100),
                ),
                commit=True,
            )

    return jsonify({"disruption": disruption, "claim": claim_result})


@app.route("/api/claims/<int:worker_id>")
def api_claims(worker_id):
    claims = db_query(
        "SELECT * FROM claims WHERE worker_id=%s ORDER BY processed_at DESC",
        (worker_id,)
    ) or []
    for c in claims:
        c["processed_at"] = c["processed_at"].strftime("%d %b %Y, %I:%M %p")
    return jsonify({"claims": claims, "total": len(claims)})


@app.route("/api/admin/stats")
def api_admin_stats():
    total_workers  = (db_query("SELECT COUNT(*) AS n FROM workers", fetch="one") or {}).get("n", 0)
    total_premium  = (db_query("SELECT COALESCE(SUM(premium),0) AS n FROM workers", fetch="one") or {}).get("n", 0)
    total_claims   = (db_query("SELECT COUNT(*) AS n FROM claims", fetch="one") or {}).get("n", 0)
    total_payout   = (db_query("SELECT COALESCE(SUM(payout_amount),0) AS n FROM claims", fetch="one") or {}).get("n", 0)
    cities         = db_query("SELECT city, COUNT(*) AS workers FROM workers GROUP BY city ORDER BY workers DESC LIMIT 6") or []
    platforms      = db_query("SELECT platform, COUNT(*) AS workers FROM workers GROUP BY platform ORDER BY workers DESC") or []
    recent_claims  = db_query(
        """SELECT c.*, w.name as worker_name, w.city
           FROM claims c JOIN workers w ON c.worker_id=w.id
           ORDER BY c.processed_at DESC LIMIT 8"""
    ) or []
    for c in recent_claims:
        c["processed_at"] = c["processed_at"].strftime("%d %b %Y, %I:%M %p")

    return jsonify({
        "total_workers":  total_workers,
        "total_premium":  int(total_premium),
        "total_claims":   total_claims,
        "total_payout":   int(total_payout),
        "weekly_revenue": int(total_premium),
        "loss_ratio":     round(int(total_payout) / max(int(total_premium) * 52, 1) * 100, 1),
        "cities":         cities,
        "platforms":      platforms,
        "recent_claims":  recent_claims,
    })


@app.route("/api/admin/workers")
def api_admin_workers():
    workers = db_query(
        """SELECT w.*, COUNT(c.id) AS claim_count, COALESCE(SUM(c.payout_amount),0) AS total_payout
           FROM workers w LEFT JOIN claims c ON w.id=c.worker_id
           GROUP BY w.id ORDER BY w.id DESC"""
    ) or []
    for w in workers:
        w["registered_at"] = w["registered_at"].strftime("%d %b %Y")
    return jsonify({"workers": workers})


@app.route("/api/admin/workers/<int:worker_id>", methods=["DELETE"])
def api_delete_worker(worker_id):
    db_query("DELETE FROM workers WHERE id=%s", (worker_id,), commit=True)
    return jsonify({"success": True, "message": f"Worker #{worker_id} deleted."})


@app.route("/api/fraud-check/<int:worker_id>")
def api_fraud_check(worker_id):
    return jsonify(fraud_analysis(worker_id))


@app.route("/api/leaderboard")
def api_leaderboard():
    rows = []
    for city, data in ZONE_RISK.items():
        risk = (data["waterlog_score"] + data["flood_history"]) / 2
        rows.append({"city": city, "risk_score": round(risk * 100), "waterlog": round(data["waterlog_score"] * 100)})
    rows.sort(key=lambda x: x["risk_score"], reverse=True)
    return jsonify({"cities": rows})


@app.route("/api/triggers")
def api_triggers():
    return jsonify({"triggers": TRIGGERS, "platforms": list(PLATFORM_RISK.keys()), "cities": list(ZONE_RISK.keys())})


@app.route("/api/health")
def api_health():
    conn = get_db()
    db_ok = conn is not None
    if conn:
        conn.close()
    return jsonify({"status": "ok" if db_ok else "db_error", "db": db_ok, "version": "Phase 2"})


# ─── Serve the single-page HTML ──────────────────────────────────────────────
from flask import send_from_directory
import os

@app.route("/")
def index():
    html_path = os.path.join(os.path.dirname(__file__), "gigshield.html")
    if os.path.exists(html_path):
        return open(html_path).read(), 200, {"Content-Type": "text/html"}
    return "<h1>GigShield API is running. Open gigshield.html in a browser.</h1>"


if __name__ == "__main__":
    print("=" * 60)
    print("  GigShield — AI Parametric Insurance  —  Phase 2")
    print("  API + SPA at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
