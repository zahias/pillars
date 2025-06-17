import streamlit as st
import sqlite3
from datetime import datetime

# ── Database helpers ──────────────────────────────────────────────────────

@st.experimental_singleton
def get_db_conn():
    conn = sqlite3.connect("pillars.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.executescript("""
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
    """)
    conn.commit()

# ── Pillars & Indicators Page ────────────────────────────────────────────

def manage_pillars_and_indicators():
    st.header("🏛️ Pillars & Indicators")

    conn = get_db_conn()
    c = conn.cursor()

    # — Pillar CRUD —
    st.subheader("Pillars")
    pillars = c.execute("SELECT * FROM pillars ORDER BY name").fetchall()
    with st.expander("Add new pillar"):
        new_name = st.text_input("Name", key="new_pillar_name")
        new_desc = st.text_area("Description", key="new_pillar_desc")
        if st.button("➕ Create pillar"):
            now = datetime.utcnow().isoformat()
            c.execute(
                "INSERT INTO pillars (name,description,created_at,updated_at) VALUES (?,?,?,?)",
                (new_name, new_desc, now, now)
            )
            conn.commit()
            st.success(f"Pillar '{new_name}' added.")
            st.experimental_rerun()

    for p in pillars:
        with st.expander(f"{p['name']}", expanded=False):
            # Edit/Delete Pillar
            col1, col2 = st.columns([3,1])
            with col1:
                updated_name = st.text_input("Name", value=p["name"], key=f"pill_nm_{p['pillar_id']}")
                updated_desc = st.text_area("Description", value=p["description"], key=f"pill_desc_{p['pillar_id']}")
            with col2:
                if st.button("🗑️ Delete", key=f"del_pill_{p['pillar_id']}"):
                    c.execute("DELETE FROM indicators WHERE pillar_id=?", (p["pillar_id"],))
                    c.execute("DELETE FROM pillars WHERE pillar_id=?", (p["pillar_id"],))
                    conn.commit()
                    st.success("Deleted.")
                    st.experimental_rerun()
            if st.button("💾 Save changes", key=f"save_pill_{p['pillar_id']}"):
                now = datetime.utcnow().isoformat()
                c.execute(
                    "UPDATE pillars SET name=?,description=?,updated_at=? WHERE pillar_id=?",
                    (updated_name, updated_desc, now, p["pillar_id"])
                )
                conn.commit()
                st.success("Updated.")
                st.experimental_rerun()

            # — Indicator CRUD under this pillar —
            st.markdown("**Indicators**")
            inds = c.execute(
                "SELECT * FROM indicators WHERE pillar_id=? ORDER BY name",
                (p["pillar_id"],)
            ).fetchall()

            with st.expander("Add new indicator", expanded=False):
                ind_name = st.text_input("Indicator name", key=f"new_ind_name_{p['pillar_id']}")
                ind_goal = st.number_input("Goal (numeric)", min_value=0, step=1, key=f"new_ind_goal_{p['pillar_id']}")
                if st.button("➕ Create indicator", key=f"create_ind_{p['pillar_id']}"):
                    now = datetime.utcnow().isoformat()
                    c.execute(
                        "INSERT INTO indicators (pillar_id,name,goal,created_at,updated_at) VALUES (?,?,?,?,?)",
                        (p["pillar_id"], ind_name, ind_goal, now, now)
                    )
                    conn.commit()
                    st.success(f"Indicator '{ind_name}' added.")
                    st.experimental_rerun()

            for ind in inds:
                cols = st.columns([3,1,1])
                with cols[0]:
                    new_ind_name = st.text_input("Name", value=ind["name"], key=f"ind_nm_{ind['indicator_id']}")
                    new_ind_goal = st.number_input("Goal", min_value=0, step=1, value=ind["goal"] or 0, key=f"ind_goal_{ind['indicator_id']}")
                with cols[1]:
                    if st.button("💾", key=f"save_ind_{ind['indicator_id']}"):
                        now = datetime.utcnow().isoformat()
                        c.execute(
                            "UPDATE indicators SET name=?,goal=?,updated_at=? WHERE indicator_id=?",
                            (new_ind_name, new_ind_goal, now, ind["indicator_id"])
                        )
                        conn.commit()
                        st.success("Saved.")
                        st.experimental_rerun()
                with cols[2]:
                    if st.button("🗑️", key=f"del_ind_{ind['indicator_id']}"):
                        c.execute("DELETE FROM indicators WHERE indicator_id=?", (ind["indicator_id"],))
                        conn.commit()
                        st.success("Deleted.")
                        st.experimental_rerun()

# ── Main ─────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Pillars Tracker", layout="wide")
    init_db()

    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", ["Pillars & Indicators"])

    if choice == "Pillars & Indicators":
        manage_pillars_and_indicators()

if __name__ == "__main__":
    main()
