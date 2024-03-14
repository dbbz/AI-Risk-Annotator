import streamlit as st
from nltk import agreement
from streamlit_gsheets import GSheetsConnection
from utils import create_side_menu, columns

st.set_page_config(
    page_title="AI Harm Annotator", layout="wide", initial_sidebar_state="collapsed"
)

create_side_menu()

st.markdown("# 🙌")
st.markdown("""### Thanks!""")

st.divider()

st.page_link(
    "pages/annotator.py",
    label="Click here to annotate the next incident",
    use_container_width=True,
    icon="✍🏻",
)

st.balloons()
