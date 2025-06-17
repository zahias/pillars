import streamlit as st
from db import get_db_conn
from datetime import datetime
import sqlite3

def pillars_indicators_page():
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
                    # delete pillar subtree
                    c.execute("DELETE FROM indicators WHERE pillar_id=?", (p["pillar_id"],))
                    c.execute(
                        "DELETE FROM detail_values WHERE entry_id IN (SELECT entry_id FROM detail_entries WHERE activity_id IN (SELECT activity_id FROM activities WHERE indicator_id IN (SELECT indicator_id FROM indicators WHERE pillar_id=?)))",
                        (p["pillar_id"],)
                    )
                    c.execute(
                        "DELETE FROM detail_entries WHERE activity_id IN (SELECT activity_id FROM activities WHERE indicator_id IN (SELECT indicator_id FROM indicators WHERE pillar_id=?))",
                        (p["pillar_id"],)
                    )
                    c.execute(
                        "DELETE FROM activities WHERE indicator_id IN (SELECT indicator_id FROM indicators WHERE pillar_id=?)",
                        (p["pillar_id"],)
                    )
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
