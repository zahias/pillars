import pandas as pd
from database import SessionLocal, Activity, Program, Indicator
import plotly.express as px

def get_activities_df(filters: dict) -> pd.DataFrame:
    db = SessionLocal()
    q = db.query(Activity, Program.code.label("program"), Indicator.name.label("indicator"))           .join(Program, Activity.program_id == Program.id)           .join(Indicator, Activity.indicator_id == Indicator.id)
    for field, val in filters.items():
        if val and hasattr(Activity, field):
            q = q.filter(getattr(Activity, field) == val)
        elif field == "program" and val != "ALL":
            q = q.filter(Program.code == val)
    df = pd.read_sql(q.statement, db.bind)
    db.close()
    return df

def plot_status_breakdown(df: pd.DataFrame):
    fig = px.histogram(df, x="indicator", color="status", barmode="group")
    return fig
