# streamlit_app.py

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ── MUST be the very first Streamlit command ────────────────────────────────
st.set_page_config(page_title="Pillars Tracker", layout="wide")

# ── Database helper: cache the connection as a resource ──────────────────────
@st.cache_resource
def get_db_conn():
    conn = sqlite3.connect("pillars.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
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
    CREATE TABLE IF NOT EXISTS activity_details (
      detail_id      INTEGER PRIMARY KEY AUTOINCREMENT,
      activity_id    INTEGER NOT NULL,
      year           INTEGER,
      quarter        TEXT,
      program_id     INTEGER,
      status         TEXT,
      trigger        TEXT,
      organization   TEXT,
      contact_person TEXT,
      position       TEXT,
      contact_info   TEXT,
      objective      TEXT,
      final_outcome  TEXT,
      comments       TEXT,
      created_at     TEXT,
      FOREIGN KEY(activity_id)  REFERENCES activities(activity_id),
      FOREIGN KEY(program_id)   REFERENCES programs(program_id)
    );
    """)
    conn.commit()

# ── Page: Import Parameters ─────────────────────────────────────────────────
def import_parameters():
    st.header("🔄 Import Parameters from Excel")
    st.markdown(
        """
Upload a **.xlsx** file with sheets **Programs**, **Pillars**, **Indicators**, and **Activities**.
Each sheet must have these columns:

- **Programs**: `name`, `description`  
- **Pillars**: `name`, `description`  
- **Indicators**: `pillar_name`, `name`, `goal`  
- **Activities**: `pillar_name`, `indicator_name`, `name`  
        """
    )
    uploaded = st.file_uploader("Choose Excel file", type=["xlsx"])
    if not uploaded:
        return

    try:
        xls = pd.ExcelFile(uploaded)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return

    conn = get_db_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    summary = {}

    # — Programs —
    if "Programs" in xls.sheet_names:
        df = pd.read_excel(xls, "Programs")
        count = 0
        for _, row in df.iterrows():
            name = str(row.get("name","")).strip()
            desc = str(row.get("description","")).strip()
            if not name:
                continue
            try:
                c.execute(
                    "INSERT INTO programs (name,description,created_at,updated_at) VALUES (?,?,?,?)",
                    (name, desc, now, now)
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        summary["Programs"] = count

    # — Pillars —
    if "Pillars" in xls.sheet_names:
        df = pd.read_excel(xls, "Pillars")
        count = 0
        for _, row in df.iterrows():
            name = str(row.get("name","")).strip()
            desc = str(row.get("description","")).strip()
            if not name:
                continue
            try:
                c.execute(
                    "INSERT INTO pillars (name,description,created_at,updated_at) VALUES (?,?,?,?)",
                    (name, desc, now, now)
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        summary["Pillars"] = count

    # — Indicators —
    if "Indicators" in xls.sheet_names:
        df = pd.read_excel(xls, "Indicators")
        count = 0
        for _, row in df.iterrows():
            pillar_nm = str(row.get("pillar_name","")).strip()
            ind_nm    = str(row.get("name","")).strip()
            goal      = row.get("goal", 0)
            if not pillar_nm or not ind_nm:
                continue
            res = c.execute(
                "SELECT pillar_id FROM pillars WHERE name=?",
                (pillar_nm,)
            ).fetchone()
            if not res:
                st.warning(f"Skipping indicator '{ind_nm}': pillar '{pillar_nm}' not found.")
                continue
            pid = res["pillar_id"]
            try:
                c.execute(
                    "INSERT INTO indicators (pillar_id,name,goal,created_at,updated_at) VALUES (?,?,?,?,?)",
                    (pid, ind_nm, int(goal), now, now)
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        summary["Indicators"] = count

    # — Activities —
    if "Activities" in xls.sheet_names:
        df = pd.read_excel(xls, "Activities")
        count = 0
        for _, row in df.iterrows():
            pillar_nm    = str(row.get("pillar_name","")).strip()
            ind_nm       = str(row.get("indicator_name","")).strip()
            act_nm       = str(row.get("name","")).strip()
            if not pillar_nm or not ind_nm or not act_nm:
                continue
            res_p = c.execute(
                "SELECT pillar_id FROM pillars WHERE name=?",
                (pillar_nm,)
            ).fetchone()
            if not res_p:
                st.warning(f"Skipping activity '{act_nm}': pillar '{pillar_nm}' not found.")
                continue
            pid = res_p["pillar_id"]
            res_i = c.execute(
                "SELECT indicator_id FROM indicators WHERE name=? AND pillar_id=?",
                (ind_nm, pid)
            ).fetchone()
            if not res_i:
                st.warning(f"Skipping activity '{act_nm}': indicator '{ind_nm}' not found under pillar '{pillar_nm}'.")
                continue
            iid = res_i["indicator_id"]
            try:
                c.execute(
                    "INSERT INTO activities (indicator_id,name,created_at,updated_at) VALUES (?,?,?,?)",
                    (iid, act_nm, now, now)
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        summary["Activities"] = count

    conn.commit()
    st.success("Import complete!")
    for k,v in summary.items():
        st.write(f"- {k}: added {v} new rows")
