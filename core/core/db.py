import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("AGENT_DB_PATH", "agent_data.db")


def get_connection(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  summary TEXT,
  detail TEXT,
  cost_usd REAL,
  status TEXT
);

CREATE TABLE IF NOT EXISTS llm_quota_ledger (
  provider TEXT PRIMARY KEY,
  model TEXT,
  limit_type TEXT,
  limit_value INTEGER,
  used_today INTEGER DEFAULT 0,
  reset_at TEXT,
  tier TEXT,
  priority_order INTEGER
);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  description TEXT,
  status TEXT,
  assigned_agent TEXT,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  amount REAL,
  source TEXT,
  type TEXT,
  tx_hash TEXT
);

CREATE TABLE IF NOT EXISTS directives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  from_agent TEXT,
  directive_type TEXT,
  related_directive_id INTEGER,
  model_used TEXT,
  action TEXT,
  reason TEXT,
  status TEXT,
  reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS config (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS vault (
  service TEXT PRIMARY KEY,
  username TEXT,
  password_encrypted TEXT,
  created_at TEXT,
  status TEXT,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER,
  task_type TEXT,
  platform TEXT,
  niche TEXT,
  price REAL,
  content_summary TEXT,
  embedding BLOB,
  posting_time TEXT,
  llm_tier_used TEXT,
  converted INTEGER,
  revenue_amount REAL,
  engagement INTEGER,
  time_to_outcome_hours REAL
);

CREATE TABLE IF NOT EXISTS improvement_suggestions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  source TEXT,
  title TEXT,
  url TEXT,
  summary TEXT,
  relevance_note TEXT,
  status TEXT
);

CREATE TABLE IF NOT EXISTS fixes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT,
  triggering_event_id INTEGER,
  diagnosis TEXT,
  fix_type TEXT,
  detail TEXT,
  status TEXT
);
"""


def init_db(db_path=None):
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def utcnow():
    return datetime.now(timezone.utc).isoformat()
