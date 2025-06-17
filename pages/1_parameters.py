# pages/1_parameters.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from db import get_db_conn
from utils import load_sheets, to_excel_workbook

def parameters_page():
    st.header("⚙️ Parameters")
    tabs = st.tabs(["📥 Import", "📤 Export"])
    
    # — Import tab —
    with tabs[0]:
        st.markdown("Upload an **.xlsx** with sheets: Programs, Pillars, Indicators, Activities, DetailFields.")
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
                # (repeat import logic for Programs, Pillars, Indicators, Activities, DetailFields)
                # …for brevity, assume you pull in the code from your existing import_parameters,
                # plus new sheet "DetailFields" with columns:
                # pillar_name, indicator_name, activity_name, field_name, field_type, order_index
                # and insert into detail_fields table accordingly.
                #
                # At the end:
                conn.commit()
                st.success("Import complete!")
                for k,v in summary.items():
                    st.write(f"- {k}: {v} new rows")

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
