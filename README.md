# GigShield Phase 2 — AI Parametric Insurance for Gig Workers

## Quick Start

### 1. Database Setup
```bash
mysql -u root -p < setup_db.sql
```
Edit `app.py` line 28 if your MySQL password differs.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server
```bash
python app.py
```

### 4. Open the app
Open `gigshield.html` in your browser **or** navigate to `http://127.0.0.1:5000`

---

## Features
- **AI Dynamic Premium** — city risk + platform + hours + monsoon season
- **5 Disruption Triggers** — Heavy Rain, Storm, Waterlogging, Heat, AQI
- **Zero-Touch Claims** — automatic on trigger, no paperwork
- **Fraud Detection** — frequency / duplicate / ratio anomaly engine
- **UPI Payout Tracker** — mock UPI settlement flow
- **Policy Document** — downloadable certificate
- **Admin Panel** — KPIs, city heatmap, platform bars, full worker table, CSV export

## Architecture
```
gigshield.html        ← Single-page frontend (all pages + modals)
app.py                ← Flask REST API (all routes)
insurance_model.py    ← ML premium engine + disruption simulation
setup_db.sql          ← MySQL schema + seed data
```

## API Endpoints
| Method | Route | Description |
|--------|-------|-------------|
| POST | /api/register | Register worker |
| GET | /api/dashboard/:id | Worker dashboard |
| POST | /api/simulate-risk/:id | Trigger disruption simulation |
| GET | /api/claims/:id | Claims history |
| GET | /api/admin/stats | Aggregate KPIs |
| GET | /api/admin/workers | All workers |
| DELETE | /api/admin/workers/:id | Delete worker |
| GET | /api/fraud-check/:id | Fraud score |
| GET | /api/leaderboard | City risk rankings |
| GET | /api/health | DB health check |
