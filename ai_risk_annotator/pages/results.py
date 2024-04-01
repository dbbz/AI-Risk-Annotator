import datetime
import hmac
import pickle
import shelve

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from nltk import agreement
from streamlit_gsheets import GSheetsConnection
from utils import (
    check_password,
    columns,
    create_side_menu,
    read_incidents_repository_from_file,
)

st.set_page_config(page_title="AI Harm Annotator", layout="wide")
pd.options.plotting.backend = "plotly"

create_side_menu()

st.markdown("# 📈")
# st.markdown("""### Results""")

if not check_password():
    st.stop()

# Connect to the Google Sheets where to store the answers
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheets. Error: " + str(e))


@st.cache_data(ttl=3600, show_spinner="Reading the annotations from Google Sheets...")
def get_results(_conn) -> pd.DataFrame:
    df_results = (
        _conn.read(
            worksheet="Annotations", ttl=30, usecols=columns, date_formatstr="%Y-%m-%d"
        )
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    # df_results.timestamp = pd.to_datetime(df_results.timestamp, unit="s")
    df_results.datetime = pd.to_datetime(df_results.datetime)
    return df_results


df_results = get_results(conn)
repository = read_incidents_repository_from_file()

# st.dataframe(df_results, use_container_width=True, hide_index=True)

with st.sidebar:
    st.divider()
    if st.button("Refresh results", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    col, _ = st.columns([10, 1])

    col.plotly_chart(
        df_results["datetime"]
        .value_counts(sort=True, ascending=True)
        .plot(kind="barh", height=300)
        .update_layout(
            showlegend=False,
            xaxis={"title": "", "visible": True, "showticklabels": True},
            yaxis={"title": "", "visible": True, "showticklabels": True},
        ),
        use_container_width=True,
    )
    min_date = df_results.datetime.min().date() - pd.Timedelta(days=1)
    max_date = df_results.datetime.max().date() + pd.Timedelta(days=1)

    selected_dates = st.slider(
        "Filtering timeline",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
    )

    df_results = df_results.loc[
        (df_results.datetime >= pd.to_datetime(selected_dates[0]))
        & (df_results.datetime <= pd.to_datetime(selected_dates[1]))
    ]

    st.divider()
    toggle_incident_filtering = st.toggle("Filter on incidents")
    selected_incident = None
    if toggle_incident_filtering:
        selected_incident = st.radio(
            "incidents_filter",
            df_results.incident_ID.unique(),
            index=None,
            label_visibility="collapsed",
            captions=repository.loc[df_results.incident_ID.unique(), "title"].to_list(),
        )

if selected_incident:
    df_results = df_results[df_results.incident_ID == selected_incident]


agreement_container = st.container()

# Show the results tbale
# st.dataframe(df_results, use_container_width=True, hide_index=True)

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


def plot_counts(df: pd.DataFrame, column: str) -> None:
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

    ####

    # group_columns = [
    #     "annotator",
    #     "incident_ID",
    #     "stakeholders",
    #     "harm_category",
    #     "harm_subcategory",
    #     "harm_type",
    # ]
    # group_columns.remove(column)

    # df_counts = (
    #     df.groupby(["incident_ID", "annotator", column])
    #     .value_counts(sort=True, ascending=True)
    #     .to_frame(name="count")
    #     .reset_index()
    # )
    # df_counts

    # st.plotly_chart(
    #     df_counts.set_index(column)["count"]
    #     .sort_values(ascending=True)
    #     .plot(kind="barh")
    #     .update_layout(
    #         showlegend=False,
    #         xaxis={"title": "", "visible": True, "showticklabels": True},
    #         yaxis={"title": "", "visible": True, "showticklabels": True},
    #     ),
    #     use_container_width=True,
    # )


tabs_list = [
    "Annotator",
    "Stakeholders",
    "Harm subcategory",
    "Harm category",
    "Harm type",
]
tabs = st.tabs(["Sankey"] + tabs_list + ["Comments"])
for i, t in enumerate(tabs_list):
    with tabs[i + 1]:
        plot_counts(df_results, t.lower().replace(" ", "_"))

# ------- sankey  --------


@st.cache_data(ttl=3600)
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


with tabs[0]:
    sankey_vars = list(map(lambda x: x.lower().replace(" ", "_"), tabs_list))
    sankey_vars.insert(0, "incident_ID")
    sankey_vars.remove("harm_type")

    sankey_vars = st.multiselect(
        "Choose at least two columns to plot",
        sankey_vars,
        default=sankey_vars,
        max_selections=5,
        help="💡 Use the text filters for better plots.",
    )

    if sankey_vars:
        sankey_cols = st.columns(len(sankey_vars))
    text_filters = {}
    for i, col in enumerate(sankey_vars):
        text_filters[col] = sankey_cols[i].text_input(
            "Text filter on " + col,
            key="text_" + col,
            help="Case-insensitive text filtering.",
        )

    if len(sankey_vars) == 1:
        st.warning("Select a second column to plot.", icon="⚠️")

    if len(sankey_vars) > 1:
        mask = np.full_like(df_results.index, True, dtype=bool)
        for col, filered_text in text_filters.items():
            if filered_text.strip():
                mask = mask & df_results[col].str.lower().str.contains(
                    filered_text.lower()
                )

        df_mask = df_results[mask]
        df_sankey = (
            df_mask.groupby(sankey_vars).size().to_frame(name="counts").reset_index()
        )

        fig = go.Figure(
            gen_sankey(
                df_sankey,
                sankey_vars,
                "counts",
                None,
            )
        )
        fig.update_layout(
            font_color="black",
            font_size=15,
        )

        st.plotly_chart(fig, use_container_width=True)


with tabs[-1]:
    df_filter = df_results[df_results.notes.notna()]

    for _, row in df_filter.iterrows():
        col_1, col_2, col_3, col_4 = st.columns([2, 2, 4, 1])
        col_1.write(repository.loc[row.incident_ID, "title"])
        col_2.write(
            f":red[{row.harm_type}] harm on :violet[{row.stakeholders}] of :blue[{row.harm_subcategory}] with the comment:"
        )
        col_3.warning(row.notes)
        col_4.write(row.annotator)


# ------- agreement --------

st.divider()


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
except Exception as e:
    st.info("The agreement analysis requires more than annotations.")
    st.toast(e)
    # st.stop()
else:
    with agreement_container:
        st.markdown("### Agreement analysis", help="Krippendorf's alpha for agreement")
        col_1, col_2 = st.columns(2)
        col_1.metric("on stakeholders", f"{alpha_stakeholder:.3f}")
        col_2.metric("on actual harm", f"{alpha_harm:.3f}")
