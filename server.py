"""server.py — GigShield Phase 2 production entry-point (Render / Gunicorn)."""
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
