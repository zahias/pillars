# Updated `streamlit_app.py`

Below is the complete, self-contained `streamlit_app.py` with the `make_excel_template()` function refactored to use a context manager (removing the call to `writer.save()`). Copy this over your existing file.

```python
import io
from datetime import datetime
from typing import Dict

import pandas as pd
import plotly.express as px
import streamlit as st

# Optional: if you want PDF export
import pdfkit

st.set_page_config(layout="wide", page_title="Pillars Dashboard")


def make_excel_template() -> bytes:
    """
    Build an in-memory Excel template with all required sheets and headers.
    Uses a context manager so no explicit save() call is required.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # Pillars Structure template
        pd.DataFrame(columns=["Pillar", "Indicator", "Actual", "Goal"]) \
            .to_excel(writer, sheet_name="Pillars Structure", index=False)
        # Activities template
        pd.DataFrame(columns=["Date", "Pillar", "Program", "Indicator"]) \
            .to_excel(writer, sheet_name="Activities", index=False)
        # Social Media template
        pd.DataFrame(columns=["Date", "Posts", "Reach"]) \
            .to_excel(writer, sheet_name="Social Media", index=False)
        # Meetings template
        pd.DataFrame(columns=["Date", "Program", "Attendees"]) \
            .to_excel(writer, sheet_name="Meetings", index=False)
        # Grants template
        pd.DataFrame(columns=["Date", "Status"]) \
            .to_excel(writer, sheet_name="Grants", index=False)
        # Documents template
        pd.DataFrame(columns=["Name", "Pillar", "Program", "Link"]) \
            .to_excel(writer, sheet_name="Documents", index=False)
    return buffer.getvalue()


def load_sheets(uploaded: io.BytesIO) -> Dict[str, pd.DataFrame]:
    """
    Read the required sheets into DataFrames, handling missing sheets gracefully.
    """
    required = [
        "Pillars Structure",
        "Activities",
        "Social Media",
        "Meetings",
        "Grants",
        "Documents",
    ]
    try:
        xl = pd.read_excel(uploaded, sheet_name=None, engine="openpyxl")
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
        return {}

    dfs = {}
    for name in required:
        if name in xl:
            dfs[name] = xl[name].copy()
        else:
            st.warning(f"Sheet '{name}' not found in uploaded file.")
            dfs[name] = pd.DataFrame()
    return dfs


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    From 'Pillars Structure' extract Pillar, Indicator, Actual, Goal, and compute %.
    """
    df = df.dropna(subset=["Pillar", "Indicator", "Actual", "Goal"])
    df["% Complete"] = (df["Actual"] / df["Goal"]).clip(upper=1.0) * 100
    return df


def make_cards(df_kpi: pd.DataFrame):
    """
    Display one st.metric card per indicator.
    """
    cols = st.columns(min(4, len(df_kpi)))
    for (idx, row), col in zip(df_kpi.iterrows(), cols):
        col.metric(
            label=f"{row.Pillar} — {row.Indicator}",
            value=f"{int(row.Actual)} / {int(row.Goal)}",
            delta=f"{row['% Complete']:.0f}%"
        )


def plot_pillar_progress(df_kpi: pd.DataFrame):
    dfm = df_kpi.melt(
        id_vars=["Pillar", "Indicator"],
        value_vars=["Actual", "Goal"],
        var_name="Type",
        value_name="Count"
    )
    fig = px.bar(
        dfm,
        x="Indicator",
        y="Count",
        color="Type",
        barmode="group",
        facet_col="Pillar",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_trends(df_act: pd.DataFrame, date_range):
    if df_act.empty:
        st.info("No activity data to plot trends.")
        return
    df = df_act.dropna(subset=["Date", "Indicator"]).copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby(["Month", "Indicator"]) \
                .size() \
                .reset_index(name="Count")
    fig = px.line(
        monthly,
        x="Month",
        y="Count",
        color="Indicator",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_program_distribution(df_act: pd.DataFrame):
    if df_act.empty:
        st.info("No activity data to plot distribution.")
        return
    df = df_act.dropna(subset=["Program"])
    dist = df.groupby("Program").size().reset_index(name="Count")
    fig = px.pie(dist, names="Program", values="Count", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)


def plot_social_media(df_sm: pd.DataFrame, date_range):
    if df_sm.empty:
        st.info("No social-media data to plot.")
        return
    df = df_sm.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    fig = px.line(
        df.sort_values("Date"),
        x="Date",
        y=["Posts", "Reach"],
        labels={"value": "Count", "variable": ""},
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_grants_funnel(df_gr: pd.DataFrame, date_range):
    if df_gr.empty:
        st.info("No grants data to plot funnel.")
        return
    df = df_gr.dropna(subset=["Date", "Status"]).copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    df["Quarter"] = df["Date"].dt.to_period("Q").dt.to_timestamp()
    summary = df.groupby(["Quarter", "Status"]).size().reset_index(name="Count")
    fig = px.bar(
        summary,
        x="Quarter",
        y="Count",
        color="Status",
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)


def generate_pdf(html: str) -> bytes:
    """
    Convert an HTML string to PDF bytes via pdfkit.
    Requires wkhtmltopdf installed on system.
    """
    return pdfkit.from_string(html, False)


def main():
    st.sidebar.header("🔧 Settings")
    template_bytes = make_excel_template()
    st.sidebar.download_button(
        "Download Excel Template",
        data=template_bytes,
        file_name="pillars_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    uploaded = st.sidebar.file_uploader(
        "Upload your Pillars Excel file", type=["xlsx"]
    )
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(datetime(datetime.now().year, 1, 1),
               datetime(datetime.now().year, 12, 31))
    )
    program_filter = st.sidebar.multiselect(
        "Filter by Program",
        options=[
            "Conflict Medicine",
            "Epidemic & Pandemic",
            "Refugee Health",
            "e-sahha",
            "Climate Health"
        ],
        default=[]
    )

    if not uploaded:
        st.info("Please upload your Excel file to see the dashboard.")
        return

    dfs = load_sheets(uploaded)
    df_pillars = compute_kpis(dfs["Pillars Structure"])
    df_activities = dfs["Activities"]
    df_social = dfs["Social Media"]
    df_grants = dfs["Grants"]

    st.title("📊 Pillars Master Tracker Dashboard")

    st.subheader("Key Performance Indicators")
    make_cards(df_pillars)

    st.subheader("Pillar Progress")
    plot_pillar_progress(df_pillars)

    st.subheader("Trend Over Time")
    plot_trends(df_activities, date_range)

    st.subheader("Program Distribution")
    plot_program_distribution(df_activities)

    st.subheader("Social Media Engagement")
    plot_social_media(df_social, date_range)

    st.subheader("Grants Funnel")
    plot_grants_funnel(df_grants, date_range)

    st.subheader("Activity Log")
    if not df_activities.empty:
        df_activities["Date"] = pd.to_datetime(df_activities["Date"])
        if program_filter:
            df_activities = df_activities[df_activities["Program"].isin(program_filter)]
        st.dataframe(df_activities)
    else:
        st.info("No activities data to show.")

    st.markdown("---")
    st.subheader("Download Full PDF Report")
    if st.button("Generate PDF"):
        html = f"""
        <h1>Pillars Dashboard Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <h2>KPI Overview</h2>
        {df_pillars.to_html(index=False)}
        """
        try:
            pdf_bytes = generate_pdf(html)
            st.download_button(
                "Download Report PDF",
                data=pdf_bytes,
                file_name="pillars_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")


if __name__ == "__main__":
    main()
