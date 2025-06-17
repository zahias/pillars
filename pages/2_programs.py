# pages/2_programs.py
import streamlit as st
from db import get_db_conn
from datetime import datetime
import sqlite3

def programs_page():
    st.header("📑 Programs")
    conn = get_db_conn()
    c = conn.cursor()
    # … (your add/edit/delete logic from manage_programs)
