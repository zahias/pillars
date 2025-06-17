# streamlit_app.py

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ── Must be the very first Streamlit command ────────────────────────────────
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
    # Core tables
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
    # Dynamic detail-entry schema
    c.executescript("""
    CREATE TABLE IF NOT EXISTS detail_fields (
      field_id     INTEGER PRIMARY KEY AUTOINCREMENT,
      activity_id  INTEGER NOT NULL,
      name         TEXT NOT NULL,
      field_type   TEXT NOT NULL,      -- "Text" or "Number"
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

# ── Import parameters from Excel ───────────────────────────────────────────
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
            name, desc = str(row.get("name","")).strip(), str(row.get("description","")).strip()
            if not name: continue
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
            name, desc = str(row.get("name","")).strip(), str(row.get("description","")).strip()
            if not name: continue
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
            pillar_nm, ind_nm, goal = str(row.get("pillar_name","")).strip(), str(row.get("name","")).strip(), row.get("goal",0)
            if not pillar_nm or not ind_nm: continue
            res = c.execute("SELECT pillar_id FROM pillars WHERE name=?", (pillar_nm,)).fetchone()
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
            pillar_nm, ind_nm, act_nm = str(row.get("pillar_name","")).strip(), str(row.get("indicator_name","")).strip(), str(row.get("name","")).strip()
            if not pillar_nm or not ind_nm or not act_nm: continue
            res_p = c.execute("SELECT pillar_id FROM pillars WHERE name=?", (pillar_nm,)).fetchone()
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
    for k, v in summary.items():
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
    for pr in c.execute("SELECT * FROM programs ORDER BY name").fetchall():
        with st.expander(pr["name"]):
            col1, col2 = st.columns([3,1])
            with col1:
                upd_name = st.text_input("Name", value=pr["name"], key=f"prog_nm_{pr['program_id']}")
                upd_desc = st.text_area("Description", value=pr["description"], key=f"prog_desc_{pr['program_id']}")
            with col2:
                if st.button("🗑️ Delete", key=f"del_prog_{pr['program_id']}"):
                    c.execute("DELETE FROM detail_values WHERE entry_id IN (SELECT entry_id FROM detail_entries WHERE program_id=?)", (pr["program_id"],))
                    c.execute("DELETE FROM detail_entries WHERE program_id=?", (pr["program_id"],))
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
    for p in c.execute("SELECT * FROM pillars ORDER BY name").fetchall():
        with st.expander(p["name"]):
            col1, col2 = st.columns([3,1])
            with col1:
                upd_nm = st.text_input("Name", value=p["name"], key=f"pill_nm_{p['pillar_id']}")
                upd_desc = st.text_area("Description", value=p["description"], key=f"pill_desc_{p['pillar_id']}")
            with col2:
                if st.button("🗑️ Delete", key=f"del_pill_{p['pillar_id']}"):
                    c.execute("DELETE FROM indicators WHERE pillar_id=?", (p["pillar_id"],))
                    c.execute("DELETE FROM detail_values WHERE entry_id IN (SELECT entry_id FROM detail_entries WHERE activity_id IN (SELECT activity_id FROM activities WHERE indicator_id IN (SELECT indicator_id FROM indicators WHERE pillar_id=?)))", (p["pillar_id"],))
                    c.execute("DELETE FROM detail_entries WHERE activity_id IN (SELECT activity_id FROM activities WHERE indicator_id IN (SELECT indicator_id FROM indicators WHERE pillar_id=?))", (p["pillar_id"],))
                    c.execute("DELETE FROM activities WHERE indicator_id IN (SELECT indicator_id FROM indicators WHERE pillar_id=?)", (p["pillar_id"],))
                    c.execute("DELETE FROM indicators WHERE pillar_id=?", (p["pillar_id"],))
                    c.execute("DELETE FROM pillars WHERE pillar_id=?", (p["pillar_id"],))
                    conn.commit()
                    st.success("Deleted pillar and all its sub-items.")
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

            # List & edit indicators
            st.markdown("**Existing indicators**")
            for ind in c.execute(
                "SELECT * FROM indicators WHERE pillar_id=? ORDER BY name", (p["pillar_id"],)
            ).fetchall():
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

# ── Page: Manage Activities & Dynamic Details ──────────────────────────────
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

    # Step 3: For each activity -> manage fields & entries
    for act in c.execute("SELECT * FROM activities WHERE indicator_id=? ORDER BY name", (iid,)).fetchall():
        with st.expander(act["name"]):
            # Rename / delete activity
            col1, col2 = st.columns([3,1])
            with col1:
                upd_act = st.text_input("Name", value=act["name"], key=f"act_nm_{act['activity_id']}")
            with col2:
                if st.button("🗑️ Delete activity", key=f"del_act_{act['activity_id']}"):
                    c.execute("DELETE FROM detail_values WHERE entry_id IN (SELECT entry_id FROM detail_entries WHERE activity_id=?)", (act["activity_id"],))
                    c.execute("DELETE FROM detail_entries WHERE activity_id=?", (act["activity_id"],))
                    c.execute("DELETE FROM detail_fields WHERE activity_id=?", (act["activity_id"],))
                    c.execute("DELETE FROM activities WHERE activity_id=?", (act["activity_id"],))
                    conn.commit()
                    st.success("Activity and all its details deleted.")
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

            # ── Manage detail-fields schema for this activity ─────────────
            st.markdown("#### 🛠 Manage detail fields")
            # List existing fields
            for fld in c.execute(
                "SELECT * FROM detail_fields WHERE activity_id=? ORDER BY order_index, field_id",
                (act["activity_id"],)
            ).fetchall():
                fcol1, fcol2, fcol3, fcol4 = st.columns([4,2,1,1])
                with fcol1:
                    new_name = st.text_input("Field name", value=fld["name"], key=f"fld_nm_{fld['field_id']}")
                with fcol2:
                    new_type = st.selectbox(
                        "Type",
                        ["Text","Number"],
                        index=0 if fld["field_type"]=="Text" else 1,
                        key=f"fld_tp_{fld['field_id']}"
                    )
                with fcol3:
                    new_order = st.number_input(
                        "Order",
                        min_value=0,
                        step=1,
                        value=fld["order_index"] or 0,
                        key=f"fld_ord_{fld['field_id']}"
                    )
                with fcol4:
                    if st.button("🗑️", key=f"del_fld_{fld['field_id']}"):
                        c.execute("DELETE FROM detail_fields WHERE field_id=?", (fld["field_id"],))
                        conn.commit()
                        st.success("Field deleted.")
                        st.rerun()
                if st.button("Save", key=f"save_fld_{fld['field_id']}"):
                    c.execute(
                        "UPDATE detail_fields SET name=?,field_type=?,order_index=? WHERE field_id=?",
                        (new_name, new_type, new_order, fld["field_id"])
                    )
                    conn.commit()
                    st.success("Field updated.")
                    st.rerun()

            # Form to add a new field
            with st.expander("➕ Add new detail field", expanded=False):
                nf_name = st.text_input("Field name", key=f"new_fld_nm_{act['activity_id']}")
                nf_type = st.selectbox("Type", ["Text","Number"], key=f"new_fld_tp_{act['activity_id']}")
                nf_order = st.number_input("Order", min_value=0, step=1, key=f"new_fld_ord_{act['activity_id']}")
                if st.button("Add field", key=f"add_fld_{act['activity_id']}"):
                    c.execute(
                        "INSERT INTO detail_fields (activity_id,name,field_type,order_index) VALUES (?,?,?,?)",
                        (act["activity_id"], nf_name, nf_type, nf_order)
                    )
                    conn.commit()
                    st.success("Field added.")
                    st.rerun()

            # ── Add detail entry with dynamic fields ───────────────────────
            st.markdown("#### ➕ Add detail entry")
            # Load schema
            schema = c.execute(
                "SELECT * FROM detail_fields WHERE activity_id=? ORDER BY order_index, field_id",
                (act["activity_id"],)
            ).fetchall()
            entry_values = {}
            for fld in schema:
                key = f"det_{fld['field_id']}_{act['activity_id']}"
                if fld["field_type"] == "Number":
                    entry_values[fld["field_id"]] = st.number_input(fld["name"], key=key)
                else:
                    entry_values[fld["field_id"]] = st.text_input(fld["name"], key=key)

            if st.button("Save detail", key=f"save_det_{act['activity_id']}"):
                now = datetime.utcnow().isoformat()
                c.execute(
                    "INSERT INTO detail_entries (activity_id,program_id,created_at) VALUES (?,?,?)",
                    (act["activity_id"], pid, now)
                )
                entry_id = c.lastrowid
                for fid, val in entry_values.items():
                    if isinstance(val, (int, float)):
                        c.execute(
                            "INSERT INTO detail_values (entry_id,field_id,value_number) VALUES (?,?,?)",
                            (entry_id, fid, val)
                        )
                    else:
                        c.execute(
                            "INSERT INTO detail_values (entry_id,field_id,value_text) VALUES (?,?,?)",
                            (entry_id, fid, val)
                        )
                conn.commit()
                st.success("Detail entry saved.")
                st.rerun()

            # ── List & delete existing detail entries ─────────────────────
            st.markdown("**Existing detail entries**")
            for en in c.execute(
                "SELECT * FROM detail_entries WHERE activity_id=? ORDER BY entry_id DESC",
                (act["activity_id"],)
            ).fetchall():
                st.markdown(f"**Entry #{en['entry_id']}** (created: {en['created_at']})")
                vals = c.execute(
                    """
                    SELECT dv.*, df.name, df.field_type
                    FROM detail_values dv
                    JOIN detail_fields df ON dv.field_id=df.field_id
                    WHERE dv.entry_id=?
                    ORDER BY df.order_index, df.field_id
                    """,
                    (en["entry_id"],)
                ).fetchall()
                for v in vals:
                    disp = v["value_number"] if v["field_type"]=="Number" else v["value_text"]
                    st.write(f"- **{v['name']}**: {disp}")
                if st.button("🗑️ Delete entry", key=f"del_en_{en['entry_id']}"):
                    c.execute("DELETE FROM detail_values WHERE entry_id=?", (en["entry_id"],))
                    c.execute("DELETE FROM detail_entries WHERE entry_id=?", (en["entry_id"],))
                    conn.commit()
                    st.success("Entry deleted.")
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
