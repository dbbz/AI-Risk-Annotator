import datetime
import hmac
import pickle
import shelve

import pandas as pd
import streamlit as st
from nltk import agreement
from streamlit_gsheets import GSheetsConnection
from utils import create_side_menu, columns

st.set_page_config(page_title="AI Harm Annotator", layout="wide")

create_side_menu()

st.markdown("# 📈")
st.markdown("""### Results""")

# Connect to the Google Sheet where to store the answers
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheet. Error: " + str(e))


with st.spinner("Reading from Google Sheet..."):
    df_results = conn.read(
        worksheet="Annotations", ttl=0, usecols=columns, date_formatstr="%Y-%m-%d"
    )
    df_results.dropna(how="all", inplace=True)

st.dataframe(df_results, use_container_width=True)

with st.sidebar:
    st.divider()
    if st.button("Refresh results", use_container_width=True):
        st.rerun()


def preprocess_data(df):
    data_dict = {}
    for _, r in df.iterrows():
        i = (
            r.incident_ID + "-" + r.annotator + "-" + str(r.timestamp)
        )  # find same incidents annotated by same person at same time (repeat annotations will be included as separate items)
        if i not in data_dict:
            data_dict[i] = {"stakeholder": r.stakeholders, "harm": r.harm_subcategory}
        else:
            data_dict[i]["stakeholder"] = (
                data_dict[i]["stakeholder"] + "|" + r.stakeholders
            )  # multiple annotations of same incident separated by pipe
            data_dict[i]["harm"] = data_dict[i]["harm"] + "|" + r.harm_subcategory
    return data_dict


def get_df(data_dict, field):
    # dictionary of labels for the chosen field (stakeholder/harm):
    # {'AIAAIC0554': {'DB': 'Vulnerable groups', 'GA': 'General public', 'CP': 'Business'}, ...}
    labels = {}
    for k, v in data_dict.items():
        incident = k.split("-")[0]  # incident id
        annotator = k.split("-")[
            1
        ]  # annotator initials (should give each annotator a uniquie id)
        label = v[field]
        if incident not in labels:
            labels[incident] = {annotator: label}
        else:
            labels[incident][annotator] = label

    # create dataframe
    #      Incident                 DB              GA              CP
    # 0  AIAAIC0554  Vulnerable groups  General public        Business
    labels_list = [[v for v in val.values()] for val in labels.values()]
    df = pd.DataFrame(
        [[key] + [v for v in val.values()] for key, val in labels.items()],
        columns=[["Incident"] + [ann for ann in val] for val in labels.values()][0],
    )
    return df


# the rest is based on https://stackoverflow.com/questions/45741934/
def create_annot(an):
    """
    Create frozensets with the unique label
    or with both labels splitting on pipe.
    Unique label has to go in a list so that
    frozenset does not split it into characters.
    """
    if "|" in str(an):
        an = frozenset(an.split("|"))
    else:
        an = frozenset([an])  # single label has to go in a list as well
    return an


def format_annots(df):
    annots = []
    for idx, row in df.iterrows():
        incident = row[0]
        for ann in row.index[1:]:
            annot_coder = [ann, incident, create_annot(row[ann])]
            annots.append(annot_coder)
    return annots


try:
    data_dict = preprocess_data(df_results)

    df_stakeholder = get_df(data_dict, "stakeholder")
    annots_stakeholder = format_annots(df_stakeholder)
    task_stakeholder = agreement.AnnotationTask()
    task_stakeholder.load_array(annots_stakeholder)
    alpha_stakeholder = task_stakeholder.alpha()

    df_harm = get_df(data_dict, "harm")
    annots_harm = format_annots(df_harm)
    task_harm = agreement.AnnotationTask()
    task_harm.load_array(annots_harm)
    alpha_harm = task_harm.alpha()
except:
    st.info("The agreement analysis requires more than annotations.")
    st.stop()

st.markdown("### Agreement analysis")
st.markdown("Krippendorf's alpha for agreement")
col_1, col_2 = st.columns(2)
col_1.metric("on stakeholders", f"{alpha_stakeholder:.3f}")
col_2.metric("on actual harm", f"{alpha_harm:.3f}")
