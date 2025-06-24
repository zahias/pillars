import streamlit as st
from dashboard import get_activities_df
from report_export import export_to_csv

st.header("Export Reports")

year = st.selectbox("Year", [2024,2025], index=1)
program = st.selectbox("Program", ["ALL","CMP","RHP","ESP","EPaPP","CHP"])
filters = {"year": year, "program": program, "indicator": None, "quarter": None, "status": None}
df = get_activities_df(filters)

csv = export_to_csv(df)
st.download_button("Download CSV", data=csv, file_name=f"{program}_{year}.csv")
