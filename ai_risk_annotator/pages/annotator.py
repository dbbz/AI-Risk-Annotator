import datetime

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_markmap import markmap
from form import (
    display_question,
    stop_condition,
    Stakeholders,
    Harms,
)
from utils import (
    check_password,
    columns,
    create_side_menu,
    get_annotated_incidents,
    get_annotators,
    get_incidents_batch,
    read_incidents_repository_from_file,
    scrap_incident_description,
    switch_page,
)

st.set_page_config(page_title="AI and Algorithmic Harm Annotator", layout="centered")
create_side_menu()
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


harms = Harms().download(conn)
stakeholders = Stakeholders().download(conn)

with st.sidebar:
    st.divider()
    st.subheader("Taxonomy overview", help="Zoom and scroll for more details")
    markmap(harms.mindmap())


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

    SUBMIT_BUTTON_MESSAGE = f"Submit your answers as **{user}**"

    if not user:
        st.stop()

    repository = read_incidents_repository_from_file()
    incidents_list = None
    if not st.sidebar.toggle("Show all incidents", False):
        try:
            incidents_list = get_incidents_batch(conn)
            incidents_list = set(incidents_list) & set(repository.index)
            incidents_list = sorted(list(incidents_list), reverse=True)
        except Exception as e:
            st.toast(
                "Cannot read the short-listed list of incidents from Google Sheets."
            )
            st.toast(e)

    if not incidents_list:
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

st.divider()

with st.container(border=False):
    incident_page = repository.loc[incident, "links"]
    st.markdown("##### Incident: " + repository.loc[incident, "title"])
    with st.container(height=None, border=False):
        st.info(scrap_incident_description(incident_page))

    st.page_link(
        incident_page,
        label="Go to the incident page",
        use_container_width=True,
        icon="🌐",
    )

st.divider()
results = []

harm_category_section = st.container(border=True)
selected_harm_categories = display_question(
    key_prefix=incident,
    question="Which :violet[category] of harms is incurred? *(multiple options are possible)*",
    description=harms.description(),
    widget_cls=st.multiselect,
    widget_kwargs=dict(
        options=harms.values(),
        default=None,
    ),
    container=harm_category_section,
    help_text=harms.description(),
    show_descriptions=show_descriptions,
)
stop_condition(not selected_harm_categories, SUBMIT_BUTTON_MESSAGE)

for harm_category in selected_harm_categories:
    left, right = st.columns((1, 35))
    left.write("↳")
    harm_subcategories_prefix = f"{incident}__{harm_category}"
    harm_subcategory_question = (
        f"Which :violet[specific] `{harm_category}` harm is incurred?"
    )
    harm_subcategories_container = right.container(border=True)

    if harm_category == "Other":
        selected_harm_subcategories = display_question(
            key_prefix=harm_subcategories_prefix,
            question=harm_subcategory_question,
            widget_cls=st.text_input,
            container=harm_subcategories_container,
        )
        selected_harm_subcategories = [selected_harm_subcategories]
    else:
        selected_harm_subcategories = display_question(
            key_prefix=harm_subcategories_prefix,
            question=harm_subcategory_question + " *(multiple options are possible)*",
            description=harms.description(harm_category),
            widget_cls=st.multiselect,
            widget_kwargs=dict(
                options=harms.values(harm_category),
                default=None,
            ),
            container=harm_subcategories_container,
            help_text=harms.description(),
            show_descriptions=show_descriptions,
        )

    harm_type = display_question(
        key_prefix=f"{incident}__{harm_category}",
        question=f"Is this `{harm_category}` harm actual or potential?",
        description=harms.description("type"),
        widget_cls=st.selectbox,
        widget_kwargs=dict(
            options=["Actual", "Potential"],
            index=None,
        ),
        container=harm_subcategories_container,
        help_text=harms.description("type"),
        show_descriptions=show_descriptions,
    )

    stop_condition(
        not selected_harm_subcategories or not harm_type, SUBMIT_BUTTON_MESSAGE
    )

    for harm_subcategory in selected_harm_subcategories:
        sub_left, sub_right = right.columns((1, 35))
        sub_left.write("↳")
        stakeholder_container = sub_right.container(border=True)
        impacted_stakeholders = display_question(
            key_prefix=f"{incident}__{harm_category}__{harm_subcategory}",
            question=f"Who are the :violet[impacted] stakeholders by `{harm_subcategory}`?",
            description=stakeholders.description(),
            widget_cls=st.multiselect,
            widget_kwargs=dict(options=stakeholders.values(), default=None),
            container=stakeholder_container,
            help_text="External stakeholder (ie. not deployers or developers) individuals, groups, communities or entities using, being targeted by, or otherwise directly or indirectly negatively affected by a technology system. \n"
            + stakeholders.description(),
            show_descriptions=show_descriptions,
        )

        stop_condition(not impacted_stakeholders, SUBMIT_BUTTON_MESSAGE)

        notes = display_question(
            key_prefix=f"{incident}__{harm_category}__{harm_subcategory}",
            question=f"*[Optional]* Any :violet[notes] on `{harm_subcategory}` and `{', '.join(impacted_stakeholders)}`?",
            widget_cls=st.text_area,
            widget_kwargs=dict(
                placeholder="E.g. missing, overlapping or unclear harm type names or definitions."
            ),
            container=stakeholder_container,
        )

        for stakeholder in impacted_stakeholders:
            results.append(
                dict(
                    datetime="",
                    annotator=user,
                    incident_ID=incident,
                    stakeholders=stakeholder,
                    harm_category=harm_category,
                    harm_subcategory=harm_subcategory,
                    harm_type=harm_type,
                    notes=notes,
                    timestamp="",
                )
            )

### Submission
submitted = st.button(
    SUBMIT_BUTTON_MESSAGE,
    type="primary",
    use_container_width=True,
)

### Upload
if submitted:
    current_datetime = datetime.datetime.now()
    timestamp = int(current_datetime.timestamp())
    current_datetime = current_datetime.strftime("%Y-%m-%d")

    df_update = pd.DataFrame(data=results, columns=columns)
    df_update.datetime = current_datetime
    df_update.timestamp = timestamp

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

    st.toast(
        "Your answers were submitted. You can select another incident to annotate."
    )

    st.session_state.submitted_incidents[user][incident] = ANNOTATED_CAPTION
    st.session_state.current_user = annotators.index(user)

    switch_page("thanks")
