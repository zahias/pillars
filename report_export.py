import pandas as pd
import io

def export_to_csv(df, filename="report.csv"):
    return df.to_csv(index=False).encode("utf-8")

def export_to_excel(df_dict: dict):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        for sheet, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    out.seek(0)
    return out
