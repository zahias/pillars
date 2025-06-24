import pandas as pd
from database import SessionLocal, Program, Indicator, Activity

def ingest_data_excel(path: str):
    xls = pd.ExcelFile(path)
    df = pd.read_excel(xls, "Activities")
    db = SessionLocal()
    for _, r in df.iterrows():
        prog = db.query(Program).filter_by(code=r.program).first()
        ind = db.query(Indicator).filter_by(name=r.indicator).first()
        a = Activity(
            year=int(r.year),
            quarter=r.quarter,
            program_id=prog.id,
            indicator_id=ind.id,
            status=r.status,
            type=r.type,
            participation=r.participation,
            format=r.format,
            title=r.title
        )
        db.add(a)
    db.commit()
    db.close()
