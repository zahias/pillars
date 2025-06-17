# streamlit_app.py
import streamlit as st
from db import init_db
from pages import (
    parameters as parameters_page,
    programs as programs_page,
    pillars_indicators as pi_page,
    activities as activities_page,
)

# ── Must be first ──────────────────────────────────────────────────────────
st.set_page_config(page_title="Pillars Tracker", layout="wide")

def main():
    init_db()
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", [
        "Parameters",
        "Programs",
        "Pillars & Indicators",
        "Activities"
    ])
    if choice == "Parameters":
        parameters_page.parameters_page()
    elif choice == "Programs":
        programs_page.programs_page()
    elif choice == "Pillars & Indicators":
        pi_page.pillars_indicators_page()
    else:
        activities_page.activities_page()

if __name__ == "__main__":
    main()
