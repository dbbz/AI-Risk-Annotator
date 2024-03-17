import datetime
import hmac
import pickle
import shelve

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from nltk import agreement
from streamlit_gsheets import GSheetsConnection
from utils import check_password, columns, create_side_menu

st.set_page_config(page_title="AI Harm Annotator", layout="wide")
pd.options.plotting.backend = "plotly"

create_side_menu()

st.markdown("# 📈")
st.markdown("""### Results""")

if not check_password():
    st.stop()

# Connect to the Google Sheets where to store the answers
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheets. Error: " + str(e))


with st.spinner("Reading from Google Sheets..."):
    df_results = (
        conn.read(
            worksheet="Annotations", ttl=30, usecols=columns, date_formatstr="%Y-%m-%d"
        )
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
        .drop("timestamp", axis=1)
    )
    # df_results.timestamp = pd.to_datetime(df_results.timestamp, unit="s")
    df_results.datetime = pd.to_datetime(df_results.datetime)

with st.sidebar:
    st.divider()
    if st.button("Refresh results", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    min_date = df_results.datetime.min().date() - pd.Timedelta(days=1)
    max_date = df_results.datetime.max().date() + pd.Timedelta(days=1)
    selected_dates = st.slider(
        "Timeline",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
    )

df_results = df_results.loc[
    (df_results.datetime >= pd.to_datetime(selected_dates[0]))
    & (df_results.datetime <= pd.to_datetime(selected_dates[1]))
]

st.dataframe(df_results, use_container_width=True, hide_index=True)
# df_results = df_results.drop_duplicates(
#     subset=[
#         "annotator",
#         "incident_ID",
#         "timestamp",
#     ],
#     keep="last",
# )

# df_results = (
#     df_results.groupby(
#         [
#             "annotator",
#             "incident_ID",
#         ],
#     )["timestamp"]
#     .max()
#     .reset_index()
# )

# st.dataframe(df_results, use_container_width=True)

# ------- plots --------


def plot_counts(df, column):
    df_counts = (
        df[column].value_counts(sort=True, ascending=True).to_frame(name="count")
    )
    st.plotly_chart(
        df_counts.plot(kind="barh").update_layout(
            showlegend=False,
            xaxis={"title": "", "visible": True, "showticklabels": True},
            yaxis={"title": "", "visible": True, "showticklabels": True},
        ),
        use_container_width=True,
    )


tabs_list = ["Stakeholders", "Harm category", "Harm subcategory", "Harm type"]
tabs = st.tabs(["Sankey"] + tabs_list)
for i, t in enumerate(tabs_list):
    with tabs[i + 1]:
        plot_counts(df_results, t.lower().replace(" ", "_"))

# ------- sankey  --------


def gen_sankey(df, cat_cols=[], value_cols="", title="Sankey Diagram"):
    color_palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    label_list = []
    color_num_list = []
    for cat_col in cat_cols:
        label_list_temp = list(set(df[cat_col].values))
        color_num_list.append(len(label_list_temp))
        label_list = label_list + label_list_temp

    # remove duplicates from label_list
    label_list = list(dict.fromkeys(label_list))

    # define colors based on number of levels
    color_list = []
    for idx, color_num in enumerate(color_num_list):
        color_list = color_list + [color_palette[idx]] * color_num

    # transform df into a source-target pair
    for i in range(len(cat_cols) - 1):
        if i == 0:
            source_target_df = df[[cat_cols[i], cat_cols[i + 1], value_cols]]
            source_target_df.columns = ["source", "target", "count"]
        else:
            temp_df = df[[cat_cols[i], cat_cols[i + 1], value_cols]]
            temp_df.columns = ["source", "target", "count"]
            source_target_df = pd.concat([source_target_df, temp_df])
        source_target_df = (
            source_target_df.groupby(["source", "target"])
            .agg({"count": "sum"})
            .reset_index()
        )

    # add index for source-target pair
    source_target_df["sourceID"] = source_target_df["source"].apply(
        lambda x: label_list.index(x)
    )
    source_target_df["targetID"] = source_target_df["target"].apply(
        lambda x: label_list.index(x)
    )

    # creating the sankey diagram
    data = dict(
        type="sankey",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=label_list,
            # color=color_list,
        ),
        link=dict(
            source=source_target_df["sourceID"],
            target=source_target_df["targetID"],
            value=source_target_df["count"],
        ),
    )

    layout = dict(title=title, font=dict(size=10), height=1200)

    fig = dict(data=[data], layout=layout)
    return fig


sankey_vars = list(map(lambda x: x.lower().replace(" ", "_"), tabs_list))
sankey_vars = ["incident_ID"] + sankey_vars
sankey_vars.remove("harm_type")

df_sankey = df_results.groupby(sankey_vars).size().to_frame(name="counts").reset_index()

fig = go.Figure(
    gen_sankey(
        df_sankey,
        sankey_vars,
        "counts",
        None,
    )
)
fig.update_layout(
    font_color="blue",
    # font_size=14,
)

with tabs[0]:
    st.plotly_chart(fig, use_container_width=True)

# ------- agreement --------


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
    # st.stop()
else:
    st.markdown("### Agreement analysis")
    st.markdown("Krippendorf's alpha for agreement")
    col_1, col_2 = st.columns(2)
    col_1.metric("on stakeholders", f"{alpha_stakeholder:.3f}")
    col_2.metric("on actual harm", f"{alpha_harm:.3f}")
