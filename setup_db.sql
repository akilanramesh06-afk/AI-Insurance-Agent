-- ============================================================
-- GigShield Phase 2 — Full Database Setup
-- Run: mysql -u root -p < setup_db.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS gig_insurance;
USE gig_insurance;

-- Workers table
CREATE TABLE IF NOT EXISTS workers (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120)  NOT NULL,
    city          VARCHAR(80)   NOT NULL,
    platform      VARCHAR(80)   NOT NULL,
    daily_income  INT           NOT NULL,
    premium       INT           NOT NULL,
    hours_per_day FLOAT         DEFAULT 8.0,
    registered_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- Claims table (zero-touch auto claims)
CREATE TABLE IF NOT EXISTS claims (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    worker_id      INT          NOT NULL,
    claim_id       VARCHAR(30)  NOT NULL UNIQUE,
    trigger_type   VARCHAR(30)  NOT NULL,
    trigger_label  VARCHAR(80)  NOT NULL,
    payout_amount  INT          NOT NULL,
    coverage_pct   INT          NOT NULL,
    status         VARCHAR(20)  DEFAULT 'AUTO_APPROVED',
    processed_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE
);

-- Demo seed data
INSERT INTO workers (name, city, platform, daily_income, premium, hours_per_day) VALUES
  ('Ravi Kumar',     'Mumbai',    'Swiggy',  950,  33, 9.0),
  ('Priya Sharma',   'Bengaluru', 'Zomato',  1350, 53, 8.0),
  ('Ankit Verma',    'Delhi',     'Amazon',  680,  20, 7.0),
  ('Sunita Rao',     'Chennai',   'Blinkit', 1100, 36, 10.0),
  ('Mohammed Asif',  'Hyderabad', 'Zepto',   1500, 58, 9.5),
  ('Kavya Nair',     'Kolkata',   'Swiggy',  800,  30, 8.0);

-- Sample claims
INSERT INTO claims (worker_id, claim_id, trigger_type, trigger_label, payout_amount, coverage_pct) VALUES
  (1, 'GS-20250601-1001', 'HEAVY_RAIN',   'Heavy Rain',         700, 100),
  (2, 'GS-20250601-1002', 'STORM',        'Storm / Cyclone',    1200, 100),
  (4, 'GS-20250602-1003', 'WATERLOGGING', 'Waterlogging Alert', 560,  80);

SHOW TABLES;
SELECT id, name, city, platform, premium FROM workers;
