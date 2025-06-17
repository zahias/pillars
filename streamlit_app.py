# streamlit_app.py

import streamlit as st
from db import init_db

# ← Correct imports from your pages folder
from pages.parameters        import parameters_page
from pages.programs          import programs_page
from pages.pillars_indicators import pillars_indicators_page
from pages.activities        import activities_page

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
        parameters_page()
    elif choice == "Programs":
        programs_page()
    elif choice == "Pillars & Indicators":
        pillars_indicators_page()
    else:
        activities_page()

if __name__ == "__main__":
    main()
