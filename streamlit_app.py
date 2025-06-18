import streamlit as st
from db import init_db
from pages.parameters         import parameters_page
from pages.programs           import programs_page
from pages.pillars_indicators import pillars_indicators_page
from pages.activities         import activities_page
from pages.data_entry         import data_entry_page

# ── Must be the first Streamlit command ────────────────────────────────────
st.set_page_config(page_title="Pillars Tracker", layout="wide")

def main():
    init_db()
    st.sidebar.title("Role")
    role = st.sidebar.radio("Select role", ["Admin", "Researcher"])

    if role == "Admin":
        st.sidebar.subheader("Admin Menu")
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

    else:  # Researcher
        st.sidebar.subheader("Researcher Menu")
        choice = st.sidebar.radio("Go to", [
            "Data Entry"
        ])
        if choice == "Data Entry":
            data_entry_page()

if __name__ == "__main__":
    main()
