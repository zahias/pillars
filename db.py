import sqlite3
from streamlit import cache_resource

@cache_resource
def get_db_conn():
    conn = sqlite3.connect("pillars.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    # core tables
    c.executescript("""
    CREATE TABLE IF NOT EXISTS programs (
      program_id   INTEGER PRIMARY KEY AUTOINCREMENT,
      name         TEXT NOT NULL UNIQUE,
      description  TEXT,
      created_at   TEXT,
      updated_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS pillars (
      pillar_id    INTEGER PRIMARY KEY AUTOINCREMENT,
      name         TEXT NOT NULL UNIQUE,
      description  TEXT,
      created_at   TEXT,
      updated_at   TEXT
    );
    CREATE TABLE IF NOT EXISTS indicators (
      indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
      pillar_id    INTEGER NOT NULL,
      name         TEXT NOT NULL,
      goal         INTEGER,
      created_at   TEXT,
      updated_at   TEXT,
      FOREIGN KEY(pillar_id) REFERENCES pillars(pillar_id)
    );
    CREATE TABLE IF NOT EXISTS activities (
      activity_id  INTEGER PRIMARY KEY AUTOINCREMENT,
      indicator_id INTEGER NOT NULL,
      name         TEXT NOT NULL,
      created_at   TEXT,
      updated_at   TEXT,
      FOREIGN KEY(indicator_id) REFERENCES indicators(indicator_id)
    );
    """)
    # dynamic-detail schema (fields, entries, values)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS detail_fields (
      field_id     INTEGER PRIMARY KEY AUTOINCREMENT,
      activity_id  INTEGER NOT NULL,
      name         TEXT NOT NULL,
      field_type   TEXT NOT NULL,
      order_index  INTEGER DEFAULT 0,
      FOREIGN KEY(activity_id) REFERENCES activities(activity_id)
    );
    CREATE TABLE IF NOT EXISTS detail_entries (
      entry_id     INTEGER PRIMARY KEY AUTOINCREMENT,
      activity_id  INTEGER NOT NULL,
      program_id   INTEGER,
      created_at   TEXT,
      FOREIGN KEY(activity_id) REFERENCES activities(activity_id),
      FOREIGN KEY(program_id)  REFERENCES programs(program_id)
    );
    CREATE TABLE IF NOT EXISTS detail_values (
      value_id     INTEGER PRIMARY KEY AUTOINCREMENT,
      entry_id     INTEGER NOT NULL,
      field_id     INTEGER NOT NULL,
      value_text   TEXT,
      value_number REAL,
      FOREIGN KEY(entry_id) REFERENCES detail_entries(entry_id),
      FOREIGN KEY(field_id) REFERENCES detail_fields(field_id)
    );
    """)
    conn.commit()
