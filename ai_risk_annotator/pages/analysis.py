import streamlit as st
import pandas as pd
import shelve
import pickle
from streamlit_gsheets import GSheetsConnection
import datetime
import hmac


st.set_page_config(page_title="AI Harm Annotator", layout="wide")


st.sidebar.page_link("app.py", label="Annotator", icon="✍🏻")
st.sidebar.page_link("pages/analysis.py", label="Results", icon="📈")

st.title("Agreement calculation")

# Connect to the Google Sheet where to store the answers
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheet. Error: " + str(e))

columns = [
    "datatime",
    "annotator",
    "incident_ID",
    "stakeholders",
    "harm_category",
    "harm_subcategory",
    "notes",
    "timestamp",
]

# df = conn.read(worksheet="Annotations", ttl=0, usecols=columns).dropna()
# st.dataframe(df, use_container_width=True, hide_index=True)

AIAAIC_SHEET_ID = "1Bn55B4xz21-_Rgdr8BBb2lt0n_4rzLGxFADMlVW0PYI"
AIAAIC_SHEET_NAME = "Repository"

url = f"https://docs.google.com/spreadsheets/d/{AIAAIC_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={AIAAIC_SHEET_NAME}"
df_ = pd.read_csv(url, skip_blank_lines=True).dropna(how="all")

st.write(df_)

with st.spinner("Reading from Google Sheet..."):
    df = conn.read(
        worksheet="Annotations", ttl=0, usecols=columns, date_formatstr="%Y-%m-%d"
    ).dropna()

st.dataframe(df, use_container_width=True)
