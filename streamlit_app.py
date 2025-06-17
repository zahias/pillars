import io
import base64
from datetime import datetime
from typing import Dict

import pandas as pd
import plotly.express as px
import streamlit as st

# Optional: if you want PDF export
import pdfkit

st.set_page_config(layout="wide", page_title="Pillars Dashboard")


def make_excel_template() -> bytes:
    buffer = io.BytesIO()
    writer = pd.ExcelWriter(buffer, engine="openpyxl")
    pd.DataFrame(columns=["Pillar", "Indicator", "Actual", "Goal"]) \
      .to_excel(writer, sheet_name="Pillars Structure", index=False)
    pd.DataFrame(columns=["Date", "Pillar", "Program", "Indicator"]) \
      .to_excel(writer, sheet_name="Activities", index=False)
    pd.DataFrame(columns=["Date", "Posts", "Reach"]) \
      .to_excel(writer, sheet_name="Social Media", index=False)
    pd.DataFrame(columns=["Date", "Program", "Attendees"]) \
      .to_excel(writer, sheet_name="Meetings", index=False)
    pd.DataFrame(columns=["Date", "Status"]) \
      .to_excel(writer, sheet_name="Grants", index=False)
    pd.DataFrame(columns=["Name", "Pillar", "Program", "Link"]) \
      .to_excel(writer, sheet_name="Documents", index=False)
    writer.save()
    return buffer.getvalue()


def load_sheets(uploaded: io.BytesIO) -> Dict[str, pd.DataFrame]:
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
        st.error(f"Failed to read Excel: {e}")
        return {}
    dfs = {}
    for name in required:
        dfs[name] = xl.get(name, pd.DataFrame()).copy()
        if dfs[name].empty:
            st.warning(f"Sheet '{name}' missing or empty.")
    return dfs


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["Pillar", "Indicator", "Actual", "Goal"])
    df["% Complete"] = (df["Actual"] / df["Goal"]).clip(upper=1.0) * 100
    return df


def make_cards(df_kpi: pd.DataFrame):
    cols = st.columns(min(4, len(df_kpi)))
    for (idx, row), col in zip(df_kpi.iterrows(), cols):
        col.metric(
            label=f"{row.Pillar} – {row.Indicator}",
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
    fig = px.bar(dfm, x="Indicator", y="Count", color="Type",
                 barmode="group", facet_col="Pillar", height=400)
    st.plotly_chart(fig, use_container_width=True)


def plot_trends(df_act: pd.DataFrame, date_range):
    if df_act.empty:
        st.info("No activity data.")
        return
    df = df_act.dropna(subset=["Date", "Indicator"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    df["Month"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby(["Month", "Indicator"]).size().reset_index(name="Count")
    fig = px.line(monthly, x="Month", y="Count",
                  color="Indicator", markers=True)
    st.plotly_chart(fig, use_container_width=True)


def plot_program_distribution(df_act: pd.DataFrame):
    if df_act.empty:
        st.info("No activity data.")
        return
    df = df_act.dropna(subset=["Program"])
    dist = df.groupby("Program").size().reset_index(name="Count")
    fig = px.pie(dist, names="Program", values="Count", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)


def plot_social_media(df_sm: pd.DataFrame, date_range):
    if df_sm.empty:
        st.info("No social-media data.")
        return
    df = df_sm.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    fig = px.line(df.sort_values("Date"), x="Date",
                  y=["Posts", "Reach"], markers=True)
    st.plotly_chart(fig, use_container_width=True)


def plot_grants_funnel(df_gr: pd.DataFrame, date_range):
    if df_gr.empty:
        st.info("No grants data.")
        return
    df = df_gr.dropna(subset=["Date", "Status"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[(df["Date"] >= date_range[0]) & (df["Date"] <= date_range[1])]
    df["Quarter"] = df["Date"].dt.to_period("Q").dt.to_timestamp()
    summary = df.groupby(["Quarter", "Status"]).size().reset_index(name="Count")
    fig = px.bar(summary, x="Quarter", y="Count",
                 color="Status", barmode="group")
    st.plotly_chart(fig, use_container_width=True)


def generate_pdf(html: str) -> bytes:
    return pdfkit.from_string(html, False)


def main():
    st.sidebar.header("🔧 Settings")
    tpl = make_excel_template()
    st.sidebar.download_button(
        "Download Excel Template",
        data=tpl,
        file_name="pillars_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    uploaded = st.sidebar.file_uploader("Upload Pillars Excel", type=["xlsx"])
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(datetime(datetime.now().year, 1, 1),
               datetime(datetime.now().year, 12, 31))
    )
    prog_filter = st.sidebar.multiselect(
        "Program Filter",
        options=[
            "Conflict Medicine", "Epidemic & Pandemic",
            "Refugee Health", "e-sahha", "Climate Health"
        ],
        default=[]
    )

    if not uploaded:
        st.info("Please upload your Excel to proceed.")
        return

    dfs = load_sheets(uploaded)
    df_kpi = compute_kpis(dfs["Pillars Structure"])
    df_act = dfs["Activities"]
    df_sm = dfs["Social Media"]
    df_gr = dfs["Grants"]

    st.title("📊 Pillars Master Tracker")

    st.subheader("🔑 KPIs")
    make_cards(df_kpi)

    st.subheader("📈 Pillar Progress")
    plot_pillar_progress(df_kpi)

    st.subheader("📅 Trend Over Time")
    plot_trends(df_act, date_range)

    st.subheader("🗂️ Program Distribution")
    plot_program_distribution(df_act)

    st.subheader("💬 Social Media")
    plot_social_media(df_sm, date_range)

    st.subheader("🎯 Grants Funnel")
    plot_grants_funnel(df_gr, date_range)

    st.subheader("📋 Activity Log")
    if not df_act.empty:
        df_act["Date"] = pd.to_datetime(df_act["Date"])
        if prog_filter:
            df_act = df_act[df_act["Program"].isin(prog_filter)]
        st.dataframe(df_act)
    else:
        st.info("No raw activity entries.")

    st.markdown("---")
    st.subheader("📄 Download PDF Report")
    if st.button("Generate PDF"):
        html = f"""
        <h1>Pillars Report</h1>
        <p>Generated {datetime.now():%Y-%m-%d %H:%M}</p>
        {df_kpi.to_html(index=False)}
        """
        try:
            pdf = generate_pdf(html)
            st.download_button(
                "Download PDF",
                data=pdf,
                file_name="pillars_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"PDF export failed: {e}")


if __name__ == "__main__":
    main()
