import streamlit as st
from config import load_config, upsert_config_from_excel
from templates import make_config_template

st.header("Configuration")

st.markdown("Download the current configuration template, edit in Excel, then re-upload to apply changes.")

if st.button("Download config template"):
    bio = make_config_template()
    st.download_button("Download .xlsx", data=bio, file_name="config_template.xlsx")

uploaded = st.file_uploader("Upload updated config .xlsx", type="xlsx")
if uploaded:
    upsert_config_from_excel(uploaded)
    st.success("Configuration updated successfully!")
