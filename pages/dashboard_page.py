import streamlit as st
from dashboard import get_activities_df, plot_status_breakdown

st.header("Dashboard")

year = st.selectbox("Year", [2024,2025], index=1)
program = st.selectbox("Program", ["ALL","CMP","RHP","ESP","EPaPP","CHP"])
indicator = st.text_input("Indicator (leave blank for all)","")

filters = {"year": year, "program": program, "indicator": indicator, "quarter": None, "status": None}
df = get_activities_df(filters)
st.dataframe(df)

fig = plot_status_breakdown(df)
st.plotly_chart(fig, use_container_width=True)
