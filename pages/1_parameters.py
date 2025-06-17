import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
from db import get_db_conn
from utils import load_sheets, to_excel_workbook

def parameters_page():
    st.header("⚙️ Parameters")
    tabs = st.tabs(["📥 Import", "📤 Export"])

    # — Import tab —
    with tabs[0]:
        st.markdown("""
Upload a **.xlsx** file with sheets **Programs**, **Pillars**, **Indicators**, **Activities**, and **DetailFields**.
Columns required:

- **Programs**: `name`, `description`  
- **Pillars**: `name`, `description`  
- **Indicators**: `pillar_name`, `name`, `goal`  
- **Activities**: `pillar_name`, `indicator_name`, `name`  
- **DetailFields**: `pillar_name`, `indicator_name`, `activity_name`, `field_name`, `field_type`, `order_index`
        """)
        uploaded = st.file_uploader("Choose Excel file", type=["xlsx"], key="param_import")
        if uploaded:
            try:
                xls = pd.ExcelFile(uploaded)
            except Exception as e:
                st.error(f"Error reading file: {e}")
            else:
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
                        ind_nm = str(row.get("name","")).strip()
                        goal = row.get("goal", 0)
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
                        ind_nm = str(row.get("indicator_name","")).strip()
                        act_nm = str(row.get("name","")).strip()
                        if not pillar_nm or not ind_nm or not act_nm:
                            continue
                        res_p = c.execute(
                            "SELECT pillar_id FROM pillars WHERE name=?", (pillar_nm,)
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

                # DetailFields
                if "DetailFields" in xls.sheet_names:
                    df = pd.read_excel(xls, "DetailFields")
                    added = 0
                    for _, row in df.iterrows():
                        pillar_nm = str(row.get("pillar_name","")).strip()
                        ind_nm = str(row.get("indicator_name","")).strip()
                        act_nm = str(row.get("activity_name","")).strip()
                        fld_nm = str(row.get("field_name","")).strip()
                        fld_tp = str(row.get("field_type","")).strip()
                        fld_ord = row.get("order_index", 0)
                        if not (pillar_nm and ind_nm and act_nm and fld_nm and fld_tp):
                            continue
                        # find IDs
                        p = c.execute("SELECT pillar_id FROM pillars WHERE name=?", (pillar_nm,)).fetchone()
                        if not p:
                            st.warning(f"Field '{fld_nm}': pillar '{pillar_nm}' missing.")
                            continue
                        pid = p["pillar_id"]
                        i = c.execute(
                            "SELECT indicator_id FROM indicators WHERE name=? AND pillar_id=?",
                            (ind_nm, pid)
                        ).fetchone()
                        if not i:
                            st.warning(f"Field '{fld_nm}': indicator '{ind_nm}' missing under '{pillar_nm}'.")
                            continue
                        iid = i["indicator_id"]
                        a = c.execute(
                            "SELECT activity_id FROM activities WHERE name=? AND indicator_id=?",
                            (act_nm, iid)
                        ).fetchone()
                        if not a:
                            st.warning(f"Field '{fld_nm}': activity '{act_nm}' missing under '{ind_nm}'.")
                            continue
                        aid = a["activity_id"]
                        try:
                            c.execute(
                                "INSERT INTO detail_fields (activity_id,name,field_type,order_index) VALUES (?,?,?,?)",
                                (aid, fld_nm, fld_tp, int(fld_ord))
                            )
                            added += 1
                        except sqlite3.IntegrityError:
                            pass
                    summary["DetailFields"] = added

                conn.commit()
                st.success("Import complete!")
                for k, v in summary.items():
                    st.write(f"- {k}: {v} new rows added")

    # — Export tab —
    with tabs[1]:
        st.markdown("Download all parameters as an Excel workbook:")
        if st.button("📤 Export parameters"):
            dfs = load_sheets()
            data = to_excel_workbook(dfs)
            st.download_button(
                label="📥 Download template",
                data=data,
                file_name="parameters_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
