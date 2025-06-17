# streamlit_app.py

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ── Must be first Streamlit command ────────────────────────────────────────
st.set_page_config(page_title="Pillars Tracker", layout="wide")

# ── Database helper: cache the connection as a resource ────────────────────
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
    st.markdown("""
Upload a **.xlsx** file with sheets **Programs**, **Pillars**, **Indicators**, and **Activities**.
Each sheet needs these columns:

- **Programs**: `name`, `description`  
- **Pillars**: `name`, `description`  
- **Indicators**: `pillar_name`, `name`, `goal`  
- **Activities**: `pillar_name`, `indicator_name`, `name`  
""")
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

    # Programs
    if "Programs" in xls.sheet_names:
        df = pd.read_excel(xls, "Programs")
        added = 0
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
                added += 1
            except sqlite3.IntegrityError:
                pass
        summary["Programs"] = added

    # Pillars
    if "Pillars" in xls.sheet_names:
        df = pd.read_excel(xls, "Pillars")
        added = 0
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
                added += 1
            except sqlite3.IntegrityError:
                pass
        summary["Pillars"] = added

    # Indicators
    if "Indicators" in xls.sheet_names:
        df = pd.read_excel(xls, "Indicators")
        added = 0
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
                added += 1
            except sqlite3.IntegrityError:
                pass
        summary["Indicators"] = added

    # Activities
    if "Activities" in xls.sheet_names:
        df = pd.read_excel(xls, "Activities")
        added = 0
        for _, row in df.iterrows():
            pillar_nm = str(row.get("pillar_name","")).strip()
            ind_nm    = str(row.get("indicator_name","")).strip()
            act_nm    = str(row.get("name","")).strip()
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
                st.warning(f"Skipping activity '{act_nm}': indicator '{ind_nm}' not found under '{pillar_nm}'.")
                continue
            iid = res_i["indicator_id"]
            try:
                c.execute(
                    "INSERT INTO activities (indicator_id,name,created_at,updated_at) VALUES (?,?,?,?)",
                    (iid, act_nm, now, now)
                )
                added += 1
            except sqlite3.IntegrityError:
                pass
        summary["Activities"] = added

    conn.commit()
    st.success("Import complete!")
    for k,v in summary.items():
        st.write(f"- {k}: {v} new rows added")

# ── Page: Manage Programs ──────────────────────────────────────────────────
def manage_programs():
    st.header("📑 Programs")
    conn = get_db_conn()
    c = conn.cursor()

    st.subheader("➕ Add a new program")
    p_name = st.text_input("Program name", key="new_prog_name")
    p_desc = st.text_area("Description", key="new_prog_desc")
    if st.button("Create program"):
        now = datetime.utcnow().isoformat()
        try:
            c.execute(
                "INSERT INTO programs (name,description,created_at,updated_at) VALUES (?,?,?,?)",
                (p_name, p_desc, now, now)
            )
            conn.commit()
            st.success(f"Program '{p_name}' added.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error(f"A program named '{p_name}' already exists.")

    st.subheader("Existing programs")
    progs = c.execute("SELECT * FROM programs ORDER BY name").fetchall()
    for pr in progs:
        with st.expander(pr["name"]):
            col1, col2 = st.columns([3,1])
            with col1:
                upd_name = st.text_input("Name", value=pr["name"], key=f"prog_nm_{pr['program_id']}")
                upd_desc = st.text_area("Description", value=pr["description"], key=f"prog_desc_{pr['program_id']}")
            with col2:
                if st.button("🗑️ Delete", key=f"del_prog_{pr['program_id']}"):
                    c.execute("DELETE FROM activity_details WHERE program_id=?", (pr["program_id"],))
                    c.execute("DELETE FROM programs WHERE program_id=?", (pr["program_id"],))
                    conn.commit()
                    st.success("Deleted program and its details.")
                    st.rerun()
            if st.button("Save changes", key=f"save_prog_{pr['program_id']}"):
                now = datetime.utcnow().isoformat()
                try:
                    c.execute(
                        "UPDATE programs SET name=?,description=?,updated_at=? WHERE program_id=?",
                        (upd_name, upd_desc, now, pr["program_id"])
                    )
                    conn.commit()
                    st.success("Program updated.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"A program named '{upd_name}' already exists.")

# ── Page: Manage Pillars & Indicators ──────────────────────────────────────
def manage_pillars_and_indicators():
    st.header("🏛️ Pillars & Indicators")
    conn = get_db_conn()
    c = conn.cursor()

    st.subheader("➕ Add a new pillar")
    new_name = st.text_input("Pillar name", key="new_pillar_name")
    new_desc = st.text_area("Description", key="new_pillar_desc")
    if st.button("Create pillar"):
        now = datetime.utcnow().isoformat()
        try:
            c.execute(
                "INSERT INTO pillars (name,description,created_at,updated_at) VALUES (?,?,?,?)",
                (new_name, new_desc, now, now)
            )
            conn.commit()
            st.success(f"Pillar '{new_name}' added.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error(f"A pillar named '{new_name}' already exists.")

    st.subheader("Existing pillars")
    pillars = c.execute("SELECT * FROM pillars ORDER BY name").fetchall()
    for p in pillars:
        with st.expander(p["name"]):
            col1, col2 = st.columns([3,1])
            with col1:
                upd_nm = st.text_input("Name", value=p["name"], key=f"pill_nm_{p['pillar_id']}")
                upd_desc = st.text_area("Description", value=p["description"], key=f"pill_desc_{p['pillar_id']}")
            with col2:
                if st.button("🗑️ Delete", key=f"del_pill_{p['pillar_id']}"):
                    c.execute("DELETE FROM indicators WHERE pillar_id=?", (p["pillar_id"],))
                    c.execute("DELETE FROM pillars WHERE pillar_id=?", (p["pillar_id"],))
                    conn.commit()
                    st.success("Deleted pillar & its indicators.")
                    st.rerun()
            if st.button("Save changes", key=f"save_pill_{p['pillar_id']}"):
                now = datetime.utcnow().isoformat()
                try:
                    c.execute(
                        "UPDATE pillars SET name=?,description=?,updated_at=? WHERE pillar_id=?",
                        (upd_nm, upd_desc, now, p["pillar_id"])
                    )
                    conn.commit()
                    st.success("Pillar updated.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"A pillar named '{upd_nm}' already exists.")

            # Inline “Add new indicator”
            st.markdown("#### ➕ Add new indicator")
            ind_name = st.text_input("Indicator name", key=f"new_ind_name_{p['pillar_id']}")
            ind_goal = st.number_input("Goal (numeric)", min_value=0, step=1, key=f"new_ind_goal_{p['pillar_id']}")
            if st.button("Create indicator", key=f"create_ind_{p['pillar_id']}"):
                now = datetime.utcnow().isoformat()
                c.execute(
                    "INSERT INTO indicators (pillar_id,name,goal,created_at,updated_at) VALUES (?,?,?,?,?)",
                    (p["pillar_id"], ind_name, ind_goal, now, now)
                )
                conn.commit()
                st.success(f"Indicator '{ind_name}' added.")
                st.rerun()

            st.markdown("**Existing indicators**")
            inds = c.execute(
                "SELECT * FROM indicators WHERE pillar_id=? ORDER BY name", (p["pillar_id"],)
            ).fetchall()
            for ind in inds:
                cols = st.columns([3,1,1])
                with cols[0]:
                    nm = st.text_input("Name", value=ind["name"], key=f"ind_nm_{ind['indicator_id']}")
                    goal = st.number_input("Goal", min_value=0, step=1, value=ind["goal"] or 0, key=f"ind_goal_{ind['indicator_id']}")
                with cols[1]:
                    if st.button("Save", key=f"save_ind_{ind['indicator_id']}"):
                        now = datetime.utcnow().isoformat()
                        c.execute(
                            "UPDATE indicators SET name=?,goal=?,updated_at=? WHERE indicator_id=?",
                            (nm, goal, now, ind["indicator_id"])
                        )
                        conn.commit()
                        st.success("Indicator updated.")
                        st.rerun()
                with cols[2]:
                    if st.button("🗑️", key=f"del_ind_{ind['indicator_id']}"):
                        c.execute("DELETE FROM indicators WHERE indicator_id=?", (ind["indicator_id"],))
                        conn.commit()
                        st.success("Indicator deleted.")
                        st.rerun()

# ── Page: Manage Activities & Details ─────────────────────────────────────
def manage_activities():
    st.header("📋 Activities & Details")
    conn = get_db_conn()
    c = conn.cursor()

    # Step 1: Select program → pillar → indicator
    progs = c.execute("SELECT * FROM programs ORDER BY name").fetchall()
    prog_map = {pr["name"]: pr["program_id"] for pr in progs}
    prog_choice = st.selectbox("Program", ["—"] + list(prog_map.keys()))
    if prog_choice == "—":
        st.info("Please add/select a Program first.")
        return
    pid = prog_map[prog_choice]

    pills = c.execute("SELECT * FROM pillars ORDER BY name").fetchall()
    pill_map = {p["name"]: p["pillar_id"] for p in pills}
    pill_choice = st.selectbox("Pillar", ["—"] + list(pill_map.keys()))
    if pill_choice == "—":
        st.info("Please select a Pillar.")
        return
    plid = pill_map[pill_choice]

    inds = c.execute("SELECT * FROM indicators WHERE pillar_id=? ORDER BY name", (plid,)).fetchall()
    ind_map = {i["name"]: i["indicator_id"] for i in inds}
    ind_choice = st.selectbox("Indicator", ["—"] + list(ind_map.keys()))
    if ind_choice == "—":
        st.info("Please select an Indicator.")
        return
    iid = ind_map[ind_choice]

    st.markdown(f"### Activities under **{ind_choice}**")

    # Step 2: Add new activity
    new_act = st.text_input("✏️ New activity name", key="new_act_name")
    if st.button("➕ Add activity"):
        now = datetime.utcnow().isoformat()
        c.execute(
            "INSERT INTO activities (indicator_id,name,created_at,updated_at) VALUES (?,?,?,?)",
            (iid, new_act, now, now)
        )
        conn.commit()
        st.success(f"Activity '{new_act}' added.")
        st.rerun()

    # List activities
    acts = c.execute("SELECT * FROM activities WHERE indicator_id=? ORDER BY name", (iid,)).fetchall()
    for act in acts:
        with st.expander(act["name"]):
            col1, col2 = st.columns([3,1])
            with col1:
                upd_act = st.text_input("Name", value=act["name"], key=f"act_nm_{act['activity_id']}")
            with col2:
                if st.button("🗑️ Delete activity", key=f"del_act_{act['activity_id']}"):
                    c.execute("DELETE FROM activity_details WHERE activity_id=?", (act["activity_id"],))
                    c.execute("DELETE FROM activities WHERE activity_id=?", (act["activity_id"],))
                    conn.commit()
                    st.success("Activity and its details deleted.")
                    st.rerun()
            if st.button("Save activity name", key=f"save_act_{act['activity_id']}"):
                now = datetime.utcnow().isoformat()
                c.execute(
                    "UPDATE activities SET name=?,updated_at=? WHERE activity_id=?",
                    (upd_act, now, act["activity_id"])
                )
                conn.commit()
                st.success("Activity renamed.")
                st.rerun()

            # Step 3: Add detail record
            st.markdown("#### ➕ Add detail entry")
            year = st.number_input("Year", min_value=2000, max_value=2100, step=1, key=f"det_year_{act['activity_id']}")
            quarter = st.selectbox("Quarter", ["Q1","Q2","Q3","Q4"], key=f"det_q_{act['activity_id']}")
            status = st.text_input("Status", key=f"det_status_{act['activity_id']}")
            trigger = st.text_input("Trigger", key=f"det_trig_{act['activity_id']}")
            org = st.text_input("Organization", key=f"det_org_{act['activity_id']}")
            contact_person = st.text_input("Contact Person", key=f"det_cp_{act['activity_id']}")
            position = st.text_input("Position", key=f"det_pos_{act['activity_id']}")
            contact_info = st.text_input("Contact Information", key=f"det_ci_{act['activity_id']}")
            objective = st.text_area("Objective", key=f"det_obj_{act['activity_id']}")
            final_outcome = st.text_area("Final Outcome", key=f"det_fo_{act['activity_id']}")
            comments = st.text_area("Comments", key=f"det_com_{act['activity_id']}")

            if st.button("Save detail", key=f"save_det_{act['activity_id']}"):
                now = datetime.utcnow().isoformat()
                c.execute("""
                  INSERT INTO activity_details
                  (activity_id, year, quarter, program_id, status, trigger, organization,
                   contact_person, position, contact_info, objective, final_outcome, comments, created_at)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                  act["activity_id"], year, quarter, pid, status, trigger, org,
                  contact_person, position, contact_info, objective, final_outcome, comments, now
                ))
                conn.commit()
                st.success("Detail saved.")
                st.rerun()

            st.markdown("**Existing detail entries**")
            dets = c.execute(
                "SELECT * FROM activity_details WHERE activity_id=? ORDER BY detail_id DESC",
                (act["activity_id"],)
            ).fetchall()
            for det in dets:
                cols = st.columns([9,1])
                with cols[0]:
                    st.markdown(f"""
- **Year:** {det['year']}  
- **Quarter:** {det['quarter']}  
- **Status:** {det['status']}  
- **Trigger:** {det['trigger']}  
- **Organization:** {det['organization']}  
- **Contact Person:** {det['contact_person']}  
- **Position:** {det['position']}  
- **Contact Info:** {det['contact_info']}  
- **Objective:** {det['objective']}  
- **Final Outcome:** {det['final_outcome']}  
- **Comments:** {det['comments']}  
                    """)
                with cols[1]:
                    if st.button("🗑️", key=f"del_det_{det['detail_id']}"):
                        c.execute("DELETE FROM activity_details WHERE detail_id=?", (det['detail_id'],))
                        conn.commit()
                        st.success("Detail deleted.")
                        st.rerun()

# ── Main ───────────────────────────────────────────────────────────────────
def main():
    init_db()
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", [
        "Import Parameters",
        "Programs",
        "Pillars & Indicators",
        "Activities"
    ])
    if choice == "Import Parameters":
        import_parameters()
    elif choice == "Programs":
        manage_programs()
    elif choice == "Pillars & Indicators":
        manage_pillars_and_indicators()
    else:
        manage_activities()

if __name__ == "__main__":
    main()
