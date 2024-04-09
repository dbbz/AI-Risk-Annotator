import datetime

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_markmap import markmap
from utils import (
    check_password,
    columns,
    create_side_menu,
    get_annotated_incidents,
    get_annotators,
    get_harm_descriptions,
    get_incidents_list,
    get_stakeholders,
    load_extra_data,
    read_incidents_repository_from_file,
    scrap_incident_description,
    # stakeholders,
    switch_page,
)

st.set_page_config(page_title="AI and Algorithmic Harm Annotator", layout="centered")
create_side_menu()
st.markdown(
    """
    <style>
        .stMultiSelect [data-baseweb=select] span{
            max-width: 250px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

ANNOTATED_CAPTION = "Annotated ✔️"


st.markdown("# ✍🏻 ")
st.markdown("### Annotations")

if not check_password():
    st.stop()

with st.sidebar:
    st.divider()
    show_descriptions = st.toggle("Show descriptions next to the questions", value=True)

# Connect to the Google Sheets where to store the answers
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheets. Error: " + str(e))
    st.info(
        "Try to refresh the page. If the problem persists please inform us via Slack."
    )
    st.stop()

try:
    harm_categories, harm_categories_descriptions = get_harm_descriptions(conn)
except Exception as e:
    st.error("Cannot connect to Google Sheets. Error: " + str(e))
    st.info(
        "Try to refresh the page. If the problem persists please inform us via Slack."
    )
    st.stop()


taxonomy_mindmap = """
---
markmap:
    colorFreezeLevel: 2
---
# AI Harm Taxonomy
"""
for k, v in harm_categories.items():
    taxonomy_mindmap += f"## {k}\n"
    for i in v:
        taxonomy_mindmap += f"### {i}\n"

with st.sidebar:
    st.divider()
    st.subheader("Taxonomy overview", help="Zoom and scroll for more details")
    markmap(taxonomy_mindmap)


with st.container(border=False):
    try:
        annotators = get_annotators(conn)
    except Exception as e:
        st.error("Cannot connect to Google Sheets. Error: " + str(e))
        st.info(
            "Try to refresh the page. If the problem persists please inform us via Slack."
        )
        st.stop()

    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    st.markdown("Your name initials")
    user = st.selectbox(
        "annotator",
        options=annotators,
        index=st.session_state.current_user,
        label_visibility="collapsed",
    )

    if not user:
        st.stop()

    repository = read_incidents_repository_from_file()
    descriptions, links = load_extra_data()

    incidents_list = None
    try:
        incidents_list = get_incidents_list(conn)
        incidents_list = set(incidents_list) & set(repository.index)
        incidents_list = sorted(list(incidents_list), reverse=True)
    except Exception as e:
        st.toast("Cannot read the short-listed list of incidents from Google Sheets.")
        st.toast(e)

    if not incidents_list:
        # User the URL parameters to filter the incidents
        # to be annotated
        # eg. for <app_url>/?id=AIAAIC1366&id=AIAAIC1365
        # only the incidents with the ids AIAAIC1366 and AIAAIC1365
        # will be shown.
        filtered_incidents = st.query_params.get_all("id")
        if filtered_incidents and set(repository.index) & set(filtered_incidents):
            incidents_list = set(repository.index) & set(filtered_incidents)
            incidents_list = sorted(list(filtered_incidents), reverse=True)
        else:
            incidents_list = sorted(list(repository.index), reverse=True)

    st.markdown("Select an incident")

    try:
        annotated_incidents = get_annotated_incidents(conn)
    except Exception as e:
        st.toast(
            "Could not read the previously annotated incidents from Google Sheets."
        )
        st.toast(e)

    if user not in annotated_incidents:
        annotated_incidents = []
    else:
        annotated_incidents = annotated_incidents[user]

    if "submitted_incidents" not in st.session_state:
        st.session_state.submitted_incidents = {}

    if user not in st.session_state.submitted_incidents:
        st.session_state.submitted_incidents[user] = {
            k: ANNOTATED_CAPTION if k in annotated_incidents else ""
            for k in incidents_list
        }

    current_incident_position = st.session_state.get("current_incident_position", None)
    if current_incident_position is not None and st.session_state.get(
        "form_submitted", False
    ):
        current_incident_position += 1
        current_incident_position %= len(incidents_list)
        st.session_state.form_submitted = False

    if len(incidents_list) <= 10:
        incident = st.radio(
            "incident",
            options=incidents_list,
            index=None,
            label_visibility="collapsed",
            horizontal=True,
            captions=st.session_state.submitted_incidents[user].values(),
        )
    else:
        incident = st.selectbox(
            "incident",
            options=incidents_list,
            index=None,
            label_visibility="collapsed",
        )
        if (
            incident
            and incident in st.session_state.submitted_incidents[user]
            and st.session_state.submitted_incidents[user][incident] != ""
        ):
            st.caption(ANNOTATED_CAPTION)
    if not incident:
        st.stop()
    st.session_state.current_incident_position = incidents_list.index(incident)

st.divider()

with st.container(border=False):
    incident_page = repository.loc[incident, "links"]
    st.markdown("##### Incident: " + repository.loc[incident, "title"])
    # if incident in descriptions:
    #     st.info(descriptions[incident])
    # else:
    with st.container(height=None, border=False):
        st.info(scrap_incident_description(incident_page))

    # st.markdown("##### Links")
    # st.warning(get_list_of_media_links(incident_page))

    st.page_link(
        incident_page,
        label="Go to the incident page",
        use_container_width=True,
        icon="🌐",
    )

# st.markdown("#### Annotations")
st.divider()

with st.container(border=True):
    stakeholders = get_stakeholders(conn)
    # Make a string containing the stakeholders descriptions
    stakeholders_help_text = ""
    for k, v in stakeholders.items():
        stakeholders_help_text += f"- **{k}**: {v}\n"

    st.markdown(
        "Who are the :red[primary] impacted stakeholders?",
        help="External stakeholder (ie. not deployers or developers) individuals, groups, communities or entities using, being targeted by, or otherwise directly or indirectly negatively affected by a technology system. \n"
        + stakeholders_help_text,
    )
    if show_descriptions:
        st.caption(stakeholders_help_text)

    impacted_stakeholders = []
    primary_impacted_stakeholder = st.selectbox(
        "primary_impacted_stakeholders",
        stakeholders.keys(),
        index=None,
        label_visibility="collapsed",
        key="primary__" + incident + "__impacted",
    )

    if primary_impacted_stakeholder:
        impacted_stakeholders.append(primary_impacted_stakeholder)
        st.markdown(
            "Are there :orange[other] impacted stakeholders? (by decreasing order of importance)"
        )
        other_impacted_stakeholder = st.multiselect(
            "other_impacted_stakeholders",
            [
                elem
                for elem in stakeholders.keys()
                if elem != primary_impacted_stakeholder
            ],
            default=None,
            label_visibility="collapsed",
            key="other__" + incident + "__impacted",
        )
        impacted_stakeholders.extend(other_impacted_stakeholder)

if not impacted_stakeholders:
    submitted = st.button(
        f"Annotator: **{user}** | Submit your answers",
        type="primary",
        use_container_width=True,
        disabled=True,
    )
    st.stop()

results = {}


for stakeholder in impacted_stakeholders:
    left, right = st.columns((1, 35))
    left.write("↳")
    results[stakeholder] = {}

    with right:
        harm_category_section = st.container(border=True)
        with harm_category_section:
            harm_category_help_text = ""
            filtered_harm_description = harm_categories_descriptions.loc[
                harm_categories.keys()
            ].to_dict()
            for k, v in filtered_harm_description.items():
                harm_category_help_text += f"- **{k}**: {v}\n"

            st.markdown(
                f"Which :violet[category] of harms impacts `{stakeholder}`? *(multiple options are possible)*",
                help=harm_category_help_text,
            )

            if show_descriptions:
                st.caption(harm_category_help_text)

            # below is a trick to prevent streamlit from deleting previous answers
            # had they disappeared from the screen temporarily
            key = f"{incident}__{stakeholder}__harm_category"
            if key in st.session_state:
                st.session_state[key] = st.session_state[key]

            harm_category = st.multiselect(
                "harm_category",
                list(harm_categories.keys()) + ["Other"],
                default=None,
                label_visibility="collapsed",
                key=key,
            )
    if not harm_category:
        submitted = st.button(
            f"Annotator: **{user}** | Submit your answers",
            type="primary",
            use_container_width=True,
            disabled=True,
        )
        st.stop()

    for harm_cat in harm_category:
        with right:
            sub_left, sub_right = st.columns((1, 35))
            sub_left.write("↳")

            with sub_right:
                with st.container(border=True):
                    key = f"{incident}__{stakeholder}__{harm_cat}__harm_subcategory"
                    if key in st.session_state:
                        st.session_state[key] = st.session_state[key]

                    if harm_cat == "Other":
                        st.markdown(
                            f"Which :orange[specific] `{harm_cat}` harm impacts `{stakeholder}`?",
                        )

                        harm_subcategory = st.text_input(
                            "harm_subcategory", label_visibility="collapsed", key=key
                        )
                    else:
                        harm_category_help_text = (
                            "Example: \n" if harm_cat == "Other" else ""
                        )
                        filtered_harm_description = harm_categories_descriptions.loc[
                            harm_categories[harm_cat]
                        ].to_dict()
                        for k, v in filtered_harm_description.items():
                            harm_category_help_text += f"- **{k}**: {v}\n"

                        st.markdown(
                            f"Which :orange[specific] `{harm_cat}` harm impacts `{stakeholder}`? *(multiple options are possible)*",
                            help=harm_category_help_text,
                        )

                        if show_descriptions:
                            st.caption(harm_category_help_text)

                        harm_subcategory = st.multiselect(
                            "harm_subcategory",
                            harm_categories[harm_cat],
                            default=None,
                            label_visibility="collapsed",
                            key=key,
                        )

                    harm_type_help_text = """
- **Actual harm**: _a negative impact recorded as having occurred_ in media reports, research papers, legal dockets, assessments/audits, etc, regarding or mentioning an incident (see below). Ideally, an actual harm will have been corroborated through public statements by the deployer or developer of the technology system, though this is not always the case.
- **Potential harm**: _a negative impact mentioned as being possible or likely but which is not recorded as having occurred_ in media reports, research papers, etc. A potential harm is sometimes referred to as a ‘risk’ or ‘hazard’ by journalists, risk managers, and others.
                    """
                    st.markdown(
                        f"Is this `{harm_cat}` harm on `{stakeholder}` actual or potential?",
                        help=harm_type_help_text,
                    )
                    if show_descriptions:
                        st.caption(harm_type_help_text)

                    key = f"{incident}__{stakeholder}__{harm_cat}__harm_type"
                    if key in st.session_state:
                        st.session_state[key] = st.session_state[key]

                    harm_type = st.selectbox(
                        "incident_type",
                        ["Actual", "Potential"],
                        index=None,
                        key=key,
                        label_visibility="collapsed",
                    )

                    key = f"{incident}__{stakeholder}__{harm_cat}__notes"
                    if key in st.session_state:
                        st.session_state[key] = st.session_state[key]

                    with st.container(border=False):
                        st.markdown("*[Optional]* Notes")
                        notes = st.text_area(
                            "Further notes",
                            placeholder="E.g. missing, overlapping or unclear harm type names or definitions.",
                            label_visibility="collapsed",
                            key=key,
                        )

        if not harm_subcategory or not harm_type:
            submitted = st.button(
                f"Annotator: **{user}** | Submit your answers",
                type="primary",
                use_container_width=True,
                disabled=True,
            )
            st.stop()
        results[stakeholder][harm_cat] = (harm_subcategory, notes, harm_type)

submitted = st.button(
    f"Annotator: **{user}** | Submit your answers",
    type="primary",
    use_container_width=True,
)
if submitted:
    current_datetime = datetime.datetime.now()
    timestamp = int(current_datetime.timestamp())
    date_format = "%Y-%m-%d"
    current_datetime = current_datetime.strftime(date_format)

    tabular_results = []
    for stakeholder, harm in results.items():
        for harm_cat, (harm_subcat_list, notes, harm_type) in harm.items():
            for harm_subcat in harm_subcat_list:
                tabular_results.append(
                    [
                        current_datetime,
                        user,
                        incident,
                        stakeholder,
                        harm_cat,
                        harm_subcat,
                        harm_type,
                        notes,
                        timestamp,
                    ]
                )

    df_update = pd.DataFrame(data=tabular_results, columns=columns)

    with st.spinner("Writing to Google Sheets..."):
        try:
            df = (
                conn.read(
                    worksheet="Annotations",
                    ttl=0,
                    usecols=columns,
                    date_formatstr="%Y-%m-%d",
                )
                .dropna(how="all", axis=0)
                .dropna(how="all", axis=1)
            )

            df = pd.concat([df, df_update], ignore_index=True)
            conn.update(worksheet="Annotations", data=df)
        except Exception as e:
            st.error("Cannot connect to Google Sheets. Error: " + str(e))
            st.info(
                "Try to refresh the page. If the problem persists please inform us via Slack.",
                icon="💡",
            )
            st.info(
                "Alternatively, you can save your data and send it offline.",
                icon="⬇️",
            )
            st.download_button(
                "Save your data",
                data=df_update.to_csv().encode("utf-8"),
                file_name=f"saved_annotations_{user}_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.stop()

        # try:
        #     user_worksheet_name = "user_" + user
        #     df_backup = (
        #         conn.read(
        #             worksheet=user_worksheet_name,
        #             data=df_update,
        #             date_formatstr="%Y-%m-%d",
        #         )
        #         .dropna(how="all", axis=0)
        #         .dropna(how="all", axis=1)
        #     )

        # except Exception as e:
        #     conn.create(worksheet=user_worksheet_name, data=df_update)
        # else:
        #     conn.update(
        #         worksheet=user_worksheet_name,
        #         data=pd.concat([df_backup, df_update], ignore_index=True),
        #     )

    st.toast(
        "Your answers were submitted. You can select another incident to annotate."
    )

    st.session_state.submitted_incidents[user][incident] = ANNOTATED_CAPTION
    st.session_state.form_submitted = True
    st.session_state.current_user = annotators.index(user)

    # st.rerun()
    switch_page("thanks")
