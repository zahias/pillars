import pandas as pd
from io import BytesIO
from db import get_db_conn

def load_sheets():
    """Read all parameter tables into DataFrames."""
    conn = get_db_conn()
    dfs = {}

    dfs["Programs"] = pd.read_sql("SELECT name,description FROM programs", conn)
    dfs["Pillars"]  = pd.read_sql("SELECT name,description FROM pillars", conn)
    dfs["Indicators"] = pd.read_sql(
        "SELECT p.name AS pillar_name, i.name, i.goal "
        "FROM indicators i JOIN pillars p ON i.pillar_id = p.pillar_id",
        conn
    )
    dfs["Activities"] = pd.read_sql(
        "SELECT p.name AS pillar_name, i.name AS indicator_name, a.name "
        "FROM activities a "
        "JOIN indicators i ON a.indicator_id = i.indicator_id "
        "JOIN pillars p ON i.pillar_id = p.pillar_id",
        conn
    )
    dfs["DetailFields"] = pd.read_sql(
        "SELECT p.name AS pillar_name, i.name AS indicator_name, a.name AS activity_name, "
        "df.name AS field_name, df.field_type, df.order_index "
        "FROM detail_fields df "
        "JOIN activities a ON df.activity_id = a.activity_id "
        "JOIN indicators i ON a.indicator_id = i.indicator_id "
        "JOIN pillars p ON i.pillar_id = p.pillar_id",
        conn
    )
    return dfs

def to_excel_workbook(dfs: dict[str, pd.DataFrame]) -> bytes:
    """Write a dict of DataFrames to an in-memory .xlsx and return bytes."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()
