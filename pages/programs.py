import streamlit as st
from db import get_db_conn
from datetime import datetime
import sqlite3

def programs_page():
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
                    # cascade delete entries & values
                    c.execute(
                        "DELETE FROM detail_values WHERE entry_id IN (SELECT entry_id FROM detail_entries WHERE program_id=?)",
                        (pr["program_id"],)
                    )
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
