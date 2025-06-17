import streamlit as st
from db import get_db_conn
from datetime import datetime
import sqlite3

def activities_page():
    st.header("📋 Activities & Details")
    conn = get_db_conn()
    c = conn.cursor()

    # Step 1: Select Program → Pillar → Indicator
    progs = c.execute("SELECT * FROM programs ORDER BY name").fetchall()
    prog_map = {p["name"]: p["program_id"] for p in progs}
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

    # Step 3: For each activity → manage fields & entries
    for act in c.execute("SELECT * FROM activities WHERE indicator_id=? ORDER BY name", (iid,)).fetchall():
        with st.expander(act["name"]):

            # Rename / delete activity
            col1, col2 = st.columns([3,1])
            with col1:
                upd_act = st.text_input(
                    "Name", value=act["name"], key=f"act_nm_{act['activity_id']}"
                )
            with col2:
                if st.button("🗑️ Delete activity", key=f"del_act_{act['activity_id']}"):
                    # cascade-delete
                    c.execute(
                        "DELETE FROM detail_values WHERE entry_id IN "
                        "(SELECT entry_id FROM detail_entries WHERE activity_id=?)",
                        (act["activity_id"],)
                    )
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
            for fld in c.execute(
                "SELECT * FROM detail_fields WHERE activity_id=? ORDER BY order_index, field_id",
                (act["activity_id"],)
            ).fetchall():
                fcol1, fcol2, fcol3, fcol4 = st.columns([4,2,1,1])
                with fcol1:
                    new_name = st.text_input(
                        "Field name", value=fld["name"], key=f"fld_nm_{fld['field_id']}"
                    )
                with fcol2:
                    new_type = st.selectbox(
                        "Type",
                        ["Text","Number"],
                        index=0 if fld["field_type"]=="Text" else 1,
                        key=f"fld_tp_{fld['field_id']}"
                    )
                with fcol3:
                    new_order = st.number_input(
                        "Order", min_value=0, step=1,
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

            # ── Add new detail-field via checkbox toggle ────────────────
            add_field = st.checkbox(
                "➕ Add new detail field",
                key=f"add_fld_chk_{act['activity_id']}"
            )
            if add_field:
                nf_name = st.text_input(
                    "Field name", key=f"new_fld_nm_{act['activity_id']}"
                )
                nf_type = st.selectbox(
                    "Type", ["Text","Number"], key=f"new_fld_tp_{act['activity_id']}"
                )
                nf_order = st.number_input(
                    "Order", min_value=0, step=1, key=f"new_fld_ord_{act['activity_id']}"
                )
                if st.button("Add field", key=f"add_fld_{act['activity_id']}"):
                    c.execute(
                        "INSERT INTO detail_fields "
                        "(activity_id,name,field_type,order_index) VALUES (?,?,?,?)",
                        (act["activity_id"], nf_name, nf_type, nf_order)
                    )
                    conn.commit()
                    st.success("Field added.")
                    st.rerun()

            # ── Add detail entry with dynamic fields ─────────────────────
            st.markdown("#### ➕ Add detail entry")
            schema = c.execute(
                "SELECT field_id,name,field_type FROM detail_fields "
                "WHERE activity_id=? ORDER BY order_index, field_id",
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
                    "INSERT INTO detail_entries (activity_id,program_id,created_at) "
                    "VALUES (?,?,?)",
                    (act["activity_id"], pid, now)
                )
                entry_id = c.lastrowid
                for fid, val in entry_values.items():
                    if isinstance(val, (int, float)):
                        c.execute(
                            "INSERT INTO detail_values (entry_id,field_id,value_number) "
                            "VALUES (?,?,?)",
                            (entry_id, fid, val)
                        )
                    else:
                        c.execute(
                            "INSERT INTO detail_values (entry_id,field_id,value_text) "
                            "VALUES (?,?,?)",
                            (entry_id, fid, val)
                        )
                conn.commit()
                st.success("Detail entry saved.")
                st.rerun()

            # ── List & delete existing detail entries ─────────────────────
            st.markdown("**Existing detail entries**")
            for en in c.execute(
                "SELECT entry_id,created_at FROM detail_entries "
                "WHERE activity_id=? ORDER BY entry_id DESC",
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
