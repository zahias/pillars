import streamlit as st
from database import init_db

st.set_page_config(page_title="Program Tracker", layout="wide")
init_db()

st.title("Program Performance Tracker")
st.markdown("""
Use the sidebar to:
- Configure your schema  
- Enter or import data  
- View dashboards  
- Export reports
""")
