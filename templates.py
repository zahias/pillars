import pandas as pd
from io import BytesIO
from config import load_config

def make_config_template() -> BytesIO:
    cfg = load_config()
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        cfg["programs"].to_excel(writer, sheet_name="Programs", index=False)
        cfg["pillars"].to_excel(writer, sheet_name="Pillars", index=False)
        cfg["indicators"].to_excel(writer, sheet_name="Indicators", index=False)
    out.seek(0)
    return out

def make_data_template() -> BytesIO:
    cfg = load_config()
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df_act = pd.DataFrame([{
            "year": "",
            "quarter": "",
            "program": "",  # to be filled by user
            "indicator": "",
            "status": "",
            "type": "",
            "participation": "",
            "format": "",
            "title": ""
        }])
        df_act.to_excel(writer, sheet_name="Activities", index=False)
    out.seek(0)
    return out
