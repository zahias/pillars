import pandas as pd
from database import SessionLocal, Program, Pillar, Indicator

def load_config():
    """Return dicts of current config."""
    db = SessionLocal()
    programs = pd.DataFrame([{"code": p.code, "name": p.name, "description": p.description} for p in db.query(Program)])
    pillars = pd.DataFrame([{"name": p.name, "description": p.description} for p in db.query(Pillar)])
    indicators = pd.DataFrame([{
        "name": i.name,
        "pillar": i.pillar.name,
        "goal_per_year": i.goal_per_year,
        "statuses": i.statuses
    } for i in db.query(Indicator)])
    db.close()
    return {"programs": programs, "pillars": pillars, "indicators": indicators}

def upsert_config_from_excel(path: str):
    """Read Excel and upsert Program/Pillar/Indicator."""
    xls = pd.ExcelFile(path)
    df_prog = pd.read_excel(xls, "Programs")
    df_pil = pd.read_excel(xls, "Pillars")
    df_ind = pd.read_excel(xls, "Indicators")

    db = SessionLocal()
    # Upsert Programs
    for _, row in df_prog.iterrows():
        p = db.query(Program).filter_by(code=row.code).first()
        if not p:
            p = Program(code=row.code, name=row.name, description=row.description)
            db.add(p)
        else:
            p.name, p.description = row.name, row.description
    # Upsert Pillars
    for _, row in df_pil.iterrows():
        p = db.query(Pillar).filter_by(name=row.name).first()
        if not p:
            p = Pillar(name=row.name, description=row.description)
            db.add(p)
        else:
            p.description = row.description
    db.commit()
    # Upsert Indicators
    for _, row in df_ind.iterrows():
        pillar = db.query(Pillar).filter_by(name=row.pillar).first()
        i = db.query(Indicator).filter_by(name=row.name).first()
        if not i:
            i = Indicator(
                name=row.name,
                pillar_id=pillar.id,
                goal_per_year=int(row.goal_per_year),
                statuses=",".join(str(s).strip() for s in row.statuses.split(","))
            )
            db.add(i)
        else:
            i.pillar_id = pillar.id
            i.goal_per_year = int(row.goal_per_year)
            i.statuses = ",".join(str(s).strip() for s in row.statuses.split(","))
    db.commit()
    db.close()
