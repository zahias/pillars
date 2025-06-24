import pandas as pd
from models import Activity, SessionLocal

def export_template(path='templates/activity_template.xlsx'):
    df = pd.DataFrame([
        {
            'Date': '2025-01-01',
            'Year': 2025,
            'Quarter': 'Q1',
            'Program Code': 'CMP',
            'Pillar Name': 'Networking & Outreach',
            'Indicator Name': 'Outreach Meetings',
            'Status': 'Planned',
            'Trigger': 'Active Search',
            'Organization': 'AUB',
            'Contact Person': 'Jane Doe',
            'Contact Info': 'jane@example.com',
            'Outcome': 'Scheduled session',
            'Comments': 'Example row'
        },
        {
            'Date': '2025-02-15',
            'Year': 2025,
            'Quarter': 'Q1',
            'Program Code': 'EPaPP',
            'Pillar Name': 'Visibility',
            'Indicator Name': 'Webinars Hosted',
            'Status': 'Completed',
            'Trigger': 'Event',
            'Organization': 'WHO',
            'Contact Person': 'John Smith',
            'Contact Info': 'john@example.com',
            'Outcome': 'Webinar held',
            'Comments': 'Example row'
        }
    ])
    df.to_excel(path, index=False)

def process_upload(df):
    session = SessionLocal()
    added, updated = 0, 0
    for _, row in df.iterrows():
        exists = session.query(Activity).filter_by(
            program_code=row['Program Code'],
            pillar_name=row['Pillar Name'],
            indicator_name=row['Indicator Name'],
            date=row['Date'],
            organization=row['Organization']
        ).first()
        if exists:
            for col in row.index:
                setattr(exists, col.lower().replace(' ', '_'), row[col])
            updated += 1
        else:
            act = Activity(
                program_code=row['Program Code'],
                pillar_name=row['Pillar Name'],
                indicator_name=row['Indicator Name'],
                date=row['Date'],
                year=row['Year'],
                quarter=row['Quarter'],
                status=row['Status'],
                trigger=row['Trigger'],
                organization=row['Organization'],
                contact_person=row['Contact Person'],
                contact_info=row['Contact Info'],
                outcome=row['Outcome'],
                comments=row['Comments']
            )
            session.add(act)
            added += 1
    session.commit()
    session.close()
    return added, updated
