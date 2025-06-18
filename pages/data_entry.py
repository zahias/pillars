import streamlit as st
from db import get_db_conn
from datetime import datetime

def data_entry_page():
    st.header("📝 Data Entry")
    conn = get_db_conn()
    c = conn.cursor()

    # 1. Select Program
    progs = c.execute("SELECT name, program_id FROM programs ORDER BY name").fetchall()
    prog_map = {r["name"]: r["program_id"] for r in progs}
    prog_choice = st.selectbox("Program", ["—"] + list(prog_map.keys()), key="de_prog")
    if prog_choice == "—":
        st.info("Please select a Program.")
        return
    pid = prog_map[prog_choice]

    # 2. Select Pillar
    pills = c.execute("SELECT name, pillar_id FROM pillars ORDER BY name").fetchall()
    pill_map = {r["name"]: r["pillar_id"] for r in pills}
    pill_choice = st.selectbox("Pillar", ["—"] + list(pill_map.keys()), key="de_pill")
    if pill_choice == "—":
        st.info("Please select a Pillar.")
        return
    plid = pill_map[pill_choice]

    # 3. Select Indicator
    inds = c.execute(
        "SELECT name, indicator_id FROM indicators WHERE pillar_id=? ORDER BY name",
        (plid,)
    ).fetchall()
    ind_map = {r["name"]: r["indicator_id"] for r in inds}
    ind_choice = st.selectbox("Indicator", ["—"] + list(ind_map.keys()), key="de_ind")
    if ind_choice == "—":
        st.info("Please select an Indicator.")
        return
    iid = ind_map[ind_choice]

    # 4. Select Activity
    acts = c.execute(
        "SELECT name, activity_id FROM activities WHERE indicator_id=? ORDER BY name",
        (iid,)
    ).fetchall()
    act_map = {r["name"]: r["activity_id"] for r in acts}
    act_choice = st.selectbox("Activity", ["—"] + list(act_map.keys()), key="de_act")
    if act_choice == "—":
        st.info("Please select an Activity.")
        return
    aid = act_map[act_choice]

    st.markdown(f"### Enter data for **{act_choice}**")

    # 5. Build dynamic form based on detail_fields
    schema = c.execute(
        "SELECT field_id, name, field_type FROM detail_fields "
        "WHERE activity_id=? ORDER BY order_index, field_id",
        (aid,)
    ).fetchall()
    entry = {}
    for fld in schema:
        key = f"de_field_{fld['field_id']}"
        if fld["field_type"] == "Number":
            entry[fld["field_id"]] = st.number_input(fld["name"], key=key)
        else:
            entry[fld["field_id"]] = st.text_input(fld["name"], key=key)

    # 6. Save button
    if st.button("Save", key=f"de_save_{aid}"):
        now = datetime.utcnow().isoformat()
        c.execute(
            "INSERT INTO detail_entries (activity_id, program_id, created_at) "
            "VALUES (?,?,?)",
            (aid, pid, now)
        )
        entry_id = c.lastrowid
        for fid, val in entry.items():
            if isinstance(val, (int, float)):
                c.execute(
                    "INSERT INTO detail_values (entry_id, field_id, value_number) "
                    "VALUES (?,?,?)",
                    (entry_id, fid, val)
                )
            else:
                c.execute(
                    "INSERT INTO detail_values (entry_id, field_id, value_text) "
                    "VALUES (?,?,?)",
                    (entry_id, fid, val)
                )
        conn.commit()
        st.success("Data saved!")
        st.rerun()

    # 7. Show existing entries
    st.markdown("#### Existing entries")
    entries = c.execute(
        "SELECT entry_id, created_at FROM detail_entries "
        "WHERE activity_id=? ORDER BY entry_id DESC",
        (aid,)
    ).fetchall()
    for en in entries:
        st.markdown(f"**Entry {en['entry_id']}** (on {en['created_at']})")
        vals = c.execute(
            """
            SELECT df.name, df.field_type, dv.value_text, dv.value_number
            FROM detail_values dv
            JOIN detail_fields df ON dv.field_id = df.field_id
            WHERE dv.entry_id=?
            ORDER BY df.order_index, df.field_id
            """,
            (en["entry_id"],)
        ).fetchall()
        for v in vals:
            disp = v["value_number"] if v["field_type"] == "Number" else v["value_text"]
            st.write(f"- **{v['name']}**: {disp}")
        if st.button("🗑️ Delete entry", key=f"de_del_{en['entry_id']}"):
            c.execute("DELETE FROM detail_values WHERE entry_id=?", (en["entry_id"],))
            c.execute("DELETE FROM detail_entries WHERE entry_id=?", (en["entry_id"],))
            conn.commit()
            st.success("Entry deleted.")
            st.rerun()
