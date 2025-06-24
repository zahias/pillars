import streamlit as st
from data_ingest import ingest_data_excel
from templates import make_data_template

st.header("Data Entry")

st.markdown("Download activity template, fill in rows, then upload.")

if st.button("Download data template"):
    bio = make_data_template()
    st.download_button("Download .xlsx", data=bio, file_name="activity_template.xlsx")

f = st.file_uploader("Upload completed data .xlsx", type="xlsx")
if f:
    ingest_data_excel(f)
    st.success("Data ingested!")
