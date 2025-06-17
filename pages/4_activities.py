# pages/4_activities.py
import streamlit as st
from db import get_db_conn
from datetime import datetime
import sqlite3

def activities_page():
    st.header("📋 Activities & Details")
    conn = get_db_conn()
    c = conn.cursor()
    # … (your manage_activities logic with dynamic detail_fields)
