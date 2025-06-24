import streamlit as st
import os
import pandas as pd
from models import SessionLocal, Program, Pillar, Indicator, Activity
import utils

# Ensure template exists
os.makedirs('templates', exist_ok=True)
template_path = 'templates/activity_template.xlsx'
if not os.path.exists(template_path):
    utils.export_template(template_path)

# --- Streamlit Layout ---
st_title = st.sidebar.selectbox('Navigation', [
    'Manage Programs', 'Manage Pillars/Indicators',
    'Log Activity', 'Bulk Upload', 'Download Template', 'Dashboard'
])
session = SessionLocal()

if st_title == 'Manage Programs':
    st.header('Manage Programs')
    with st.form('prog_form'):
        code = st.text_input('Code')
        name = st.text_input('Name')
        desc = st.text_area('Description')
        if st.form_submit_button('Add Program'):
            session.add(Program(code=code, name=name, description=desc))
            session.commit()
            st.success('Program added')
    progs = session.query(Program).all()
    st.table(pd.DataFrame([{'Code': p.code, 'Name': p.name} for p in progs]))

elif st_title == 'Manage Pillars/Indicators':
    st.header('Pillars & Indicators')
    st.info('To implement: CRUD for pillars and indicators')

elif st_title == 'Log Activity':
    st.header('Log a Single Activity')
    with st.form('act_form'):
        df_cols = pd.read_excel(template_path, nrows=0).columns
        inputs = {}
        for col in df_cols:
            inputs[col] = st.text_input(col)
        if st.form_submit_button('Save Activity'):
            row = {k: inputs[k] for k in inputs}
            df = pd.DataFrame([row])
            added, updated = utils.process_upload(df)
            st.success(f"{added} added, {updated} updated")

elif st_title == 'Bulk Upload':
    st.header('Bulk Upload Activities')
    upload = st.file_uploader('Upload Excel (.xlsx)', type='xlsx')
    if upload:
        df = pd.read_excel(upload)
        added, updated = utils.process_upload(df)
        st.success(f"{added} added, {updated} updated")

elif st_title == 'Download Template':
    st.header('Download Template')
    with open(template_path, 'rb') as f:
        st.download_button('Download .xlsx Template', f, file_name='activity_template.xlsx')

else:
    st.header('Dashboard')
    acts = pd.read_sql(session.query(Activity).statement, session.bind)
    summary = acts.groupby('program_code').size()
    st.bar_chart(summary)

session.close()
