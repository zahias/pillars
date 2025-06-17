import streamlit as st
import pandas as pd
import io
import altair as alt

st.set_page_config(page_title="Pillars Tracker", layout="wide")

# Initialize session state for the Excel data
if "excel_data" not in st.session_state:
    st.session_state.excel_data = {}

st.title("Program Pillars Tracker")

# Sidebar: upload or download current config
with st.sidebar:
    st.header("Configuration File")
    uploaded = st.file_uploader("Upload Excel config/data file", type=["xlsx"], key="uploader")
    if uploaded is not None:
        try:
            st.session_state.excel_data = pd.read_excel(uploaded, sheet_name=None)
            st.success("Loaded Excel file with sheets: {}".format(
                ", ".join(st.session_state.excel_data.keys())
            ))
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
    elif not st.session_state.excel_data:
        st.info("Please upload a configuration Excel file.")

    if st.session_state.excel_data:
        # Offer download of current state
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine="openpyxl") as writer:
            for sheet, df in st.session_state.excel_data.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
            writer.save()
            towrite.seek(0)
        st.download_button(
            label="Download updated Excel",
            data=towrite,
            file_name="updated_pillars_tracker.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Main app once data is loaded
if st.session_state.excel_data:
    tabs = st.tabs(["Configuration", "Data", "Reporting"])

    # Configuration tab: edit all sheets
    with tabs[0]:
        st.header("Configuration Editor")
        st.write("Edit any sheet values. Changes will persist until you download the updated file.")
        for sheet_name, df in st.session_state.excel_data.items():
            with st.expander(f"Edit Sheet: {sheet_name}", expanded=False):
                edited_df = st.data_editor(df, use_container_width=True)
                st.session_state.excel_data[sheet_name] = edited_df

    # Data tab: specifically Activities or user-chosen
    with tabs[1]:
        st.header("Data Editor")
        sheet_list = list(st.session_state.excel_data.keys())
        data_sheet = st.selectbox("Select data sheet for activities/logs", sheet_list)
        df_data = st.session_state.excel_data[data_sheet]
        edited_data = st.data_editor(df_data, use_container_width=True)
        st.session_state.excel_data[data_sheet] = edited_data

    # Reporting tab
    with tabs[2]:
        st.header("Reporting & Visualization")
        st.write("Select sheet and fields to generate summary charts and tables.")
        sheet_for_report = st.selectbox("Sheet for reporting", list(st.session_state.excel_data.keys()))
        df_report = st.session_state.excel_data[sheet_for_report]
        if not df_report.empty:
            st.markdown("---")
            st.subheader("Pivot Table")
            cols = df_report.columns.tolist()
            row_dim = st.selectbox("Rows", cols, index=0)
            col_dim = st.selectbox("Columns", cols, index=1)
            val_field = st.selectbox("Values (numeric)", [c for c in cols if pd.api.types.is_numeric_dtype(df_report[c])], index=0)
            agg_func = st.selectbox("Aggregation", ["sum", "mean", "count"], index=0)

            pivot = pd.pivot_table(
                df_report,
                values=val_field,
                index=[row_dim],
                columns=[col_dim],
                aggfunc=agg_func,
                fill_value=0,
            )
            st.dataframe(pivot)

            st.subheader("Chart")
            pivot_reset = pivot.reset_index().melt(id_vars=row_dim)
            chart = alt.Chart(pivot_reset).mark_bar().encode(
                x=row_dim,
                y='value:Q',
                color='variable:N',
                tooltip=[row_dim, 'variable', 'value'],
            ).properties(width=700, height=400)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("The selected sheet is empty.")

else:
    st.write("Upload a valid Excel file to get started.")
