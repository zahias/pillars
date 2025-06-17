import streamlit as st
import pandas as pd
import io
import altair as alt

st.set_page_config(page_title="Pillars & Programs Tracker", layout="wide")
st.title("Pillars & Programs Tracker")

# ---- Upload & Load Excel ----
uploaded_file = st.file_uploader("Upload your Pillars Excel file", type=["xlsx"])
if not uploaded_file:
    st.info("Please upload an Excel file to get started.")
    st.stop()

@st.cache_data(show_spinner=False)
def load_excel(file) -> dict:
    xls = pd.ExcelFile(file)
    return {sheet: xls.parse(sheet) for sheet in xls.sheet_names}

if "excel_data" not in st.session_state:
    st.session_state.excel_data = load_excel(uploaded_file)

# ---- Main Tabs ----
tab1, tab2 = st.tabs(["Configuration & Data", "Reporting"])

with tab1:
    st.header("🔧 Configuration & Data")
    st.markdown(
        """
        - Edit any sheet by expanding it below.  
        - Changes are stored in-session automatically.  
        - When you’re done, use the button at the bottom to download your updated workbook.
        """
    )
    # Show each sheet in an expander with a data editor
    for sheet_name, df in st.session_state.excel_data.items():
        with st.expander(sheet_name, expanded=False):
            edited_df = st.data_editor(
                df,
                key=sheet_name,
                num_rows="dynamic",
                use_container_width=True
            )
            # Persist edits
            st.session_state.excel_data[sheet_name] = edited_df

    # Download button
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine="openpyxl") as writer:
        for sheet, df in st.session_state.excel_data.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    # No writer.save() needed
    towrite.seek(0)
    st.download_button(
        label="💾 Download Updated Excel",
        data=towrite,
        file_name="pillars_data_updated.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab2:
    st.header("📊 Reporting")
    st.markdown(
        """
        Generate pivot summaries and bar charts for any numeric indicator.
        """
    )

    sheet = st.selectbox("Choose sheet", list(st.session_state.excel_data.keys()))
    df_report = st.session_state.excel_data[sheet]

    # Identify numeric columns
    numeric_cols = df_report.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.warning(f"No numeric columns found in **{sheet}** for reporting.")
    else:
        num_col = st.selectbox("Numeric field to summarize", numeric_cols)
        # Allow grouping
        groupable = [c for c in df_report.columns if c != num_col]
        group_cols = st.multiselect("Group by (optional)", groupable)

        if st.button("▶️ Generate Report"):
            # Build pivot
            if group_cols:
                pivot = df_report.groupby(group_cols)[num_col].sum().reset_index()
            else:
                pivot = pd.DataFrame({num_col: [df_report[num_col].sum()]})

            st.subheader("Pivot Table")
            st.dataframe(pivot, use_container_width=True)

            st.subheader("Bar Chart")
            if group_cols:
                x_enc = alt.X(group_cols[0], type="nominal", axis=alt.Axis(labelAngle=-45))
            else:
                x_enc = alt.X(num_col, type="nominal")

            chart = (
                alt.Chart(pivot)
                .mark_bar()
                .encode(
                    x=x_enc,
                    y=alt.Y(num_col, type="quantitative"),
                    tooltip=group_cols + [num_col],
                )
                .properties(width="container", height=400)
            )
            st.altair_chart(chart, use_container_width=True)
