import streamlit as st
import pandas as pd
import shelve
from streamlit_gsheets import GSheetsConnection
import datetime

annotators = ["CP", "DB", "EP", "JH", "GA", "HP", "LW", "MS", "PN", "TC", "TD", "US"]

harm_categories = {
    "Autonomy": [
        "Autonomy/agency loss",
        "Impersonation/identity theft",
        "IP/copyright loss",
        "Personality loss",
    ],
    "Physical": [
        "Bodily injury",
        "Loss of life",
        "Personal health deterioration",
        "Property damage",
    ],
    "Emotional & psychological": [
        "Addiction",
        "Alienation/isolation",
        "Anxiety/distress/depression",
        "Coercion/manipulation",
        "Dehumanisation/objectification",
        "Dignity loss",
        "Divination/fetishisation",
        "Intimidation",
        "Over-reliance",
        "Radicalisation",
        "Self-harm",
        "Sexualisation",
    ],
    "Reputational": [
        "Defamation/libel/slander",
        "Loss of confidence/trust",
    ],
    "Financial & business": [
        "Business operations/infrastructure damage",
        "Confidentiality loss",
        "Competition/collusion",
        "Financial/earnings loss",
        "Livelihood loss",
        "Loss of productivity",
        "Opportunity loss",
    ],
    "Human rights & civil liberties": [
        "Loss of human rights and freedoms",
        "Benefits/entitlements loss",
        "Discrimination",
        "Privacy loss",
    ],
    "Societal & cultural": [
        "Damage to public health",
        "Information ecosystem degradation",
        "Job loss/losses",
        "Labour exploitation",
        "Loss of creativity/critical thinking",
        "Stereotyping",
        "Public service delivery deterioration",
        "Societal destabilisation",
        "Societal inequality",
        "Violence/armed conflict",
    ],
    "Political & economic": [
        "Critical infrastructure damage",
        "Economic/political power concentration",
        "Economic instability",
        "Electoral interference",
        "Institutional trust loss",
        "Political instability",
        "Political manipulation",
    ],
    "Environmental": [
        "Carbon emissions",
        "Ecology/biodiversity loss",
        "Energy consumption",
        "Natural resources extraction",
        "Electronic waste",
        "Landfill",
        "Pollution",
        "Water consumption",
    ],
    "Other": ["Cheating/plagiarism"],
}

stakeholders = {
    "Users": "Individuals or entities directly interacting with a system, or those being directly targeted by it, such as citizens, consumers, patients, students, employees, delivery drivers, job applicants, travellers, immigrants",
    "General public": "Individuals indirectly impacted by a system, such as passers-by, local communities and other members of the general public",
    "Vulnerable groups": "Including women, children, disabled people, ethnic and religious minorities",
    "Workers": "Third-party contractors and others tasked with training, managing or optimising data or information systems",
    "Artists/content creators": "People inventing, producing or making creative and/or IP/copyright-protected products, services, or content",
    "Government/public sector": "Including politicians, civil servants, and regulators",
    "Business": "Competitors, industry, and other commercial entities that are not developers or deployers of a system",
    "Investors": "Shareholders/investors in the developer and/or deployer",
}

stakeholders_help_text = ""
for k, v in stakeholders.items():
    stakeholders_help_text += f"- **{k}**: {v}\n"


@st.cache_data
def load_extra_data():
    with shelve.open("description", "r") as db:
        # df_descriptions = pd.DataFrame.from_dict(
        #     dict(db), columns=["description"], orient="index"
        # )
        descriptions = dict(db)
    with shelve.open("links", "r") as db:
        # df_links = pd.DataFrame.from_dict(dict(db), columns=["links"], orient="index")
        links = dict(db)

    return descriptions, links


@st.cache_data
def load_incidents_repository():
    df = pd.read_csv("repository.csv").dropna(how="all")
    df = df.set_index(df.columns[0])[["Headline/title", "Description/links"]]
    df.columns = ["title", "links"]
    return df


with st.empty():
    st.title("AI Risk Taxonomy")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheet. Error: " + str(e))

data = conn.read(
    worksheet="Annotations",
    # usecols=[0, 1],
    ttl="5m",
)
st.dataframe(data)


results = []

with st.container(border=True):
    st.markdown("Your name initials")
    user = st.selectbox(
        "annotator", options=annotators, index=None, label_visibility="collapsed"
    )

    if not user:
        st.stop()
    repository = load_incidents_repository()
    descriptions, links = load_extra_data()

    # User the URL parameters to filter the incidents
    # to be annotated
    # eg. for <app_url>/?id=AIAAIC1366&id=AIAAIC1365
    # only the incidents with the ids AIAAIC1366 and AIAAIC1365
    # will be shown.
    filtered_incidents = st.query_params.get_all("id")
    if filtered_incidents and set(repository.index) & set(filtered_incidents):
        incidents_list = filtered_incidents
    else:
        incidents_list = list(repository.index)

    st.markdown("Select an incident")
    incident = st.selectbox(
        "incident",
        options=incidents_list,
        index=None,
        label_visibility="collapsed",
    )
    if not incident:
        st.stop()

st.markdown("#### Incident description")

with st.container(border=True):
    st.markdown("##### " + repository.loc[incident, "title"])
    if incident in descriptions:
        st.info(descriptions[incident])
    else:
        st.warning("Description missing.")
    st.markdown("##### Links")
    if incident in links:
        st.write("\n".join(map(lambda x: "- " + x, links[incident])))

    st.link_button(
        "Go to the incident page",
        repository.loc[incident, "links"],
        use_container_width=True,
    )

st.markdown("#### Annotations")
with st.container(border=True):
    st.markdown(
        "Who are the impacted stakeholders? *(multiple options are possible)*",
        help="Stakeholders directly or indirectly impacted by incident/issue. \n"
        + stakeholders_help_text,
    )
    impacted_stakeholder = st.multiselect(
        "impacted_stakeholders",
        stakeholders.keys(),
        default=None,
        label_visibility="collapsed",
    )
    if not impacted_stakeholder:
        st.stop()

for stakeholder in impacted_stakeholder:
    with st.container(border=True):
        st.markdown(
            f"What category of harm impacts `{stakeholder}`? *(multiple options are possible)*",
            help="Stated actual negative impact(s) of incident/issue",
        )
        harm_category = st.multiselect(
            "harm_category",
            harm_categories.keys(),
            default=None,
            label_visibility="collapsed",
            key="harm_category_" + stakeholder,
        )
        if not harm_category:
            st.stop()

        for harm_cat in harm_category:
            st.markdown(
                f"What specific `{harm_cat}` harm impacts `{stakeholder}`? *(multiple options are possible)*",
                help="Stated specific negative impact(s) of incident/issue",
            )
            harm_subcategory = st.multiselect(
                "harm_subcategory",
                harm_categories[harm_cat],
                default=None,
                label_visibility="collapsed",
                key="harm_subcategory_" + stakeholder + harm_cat,
            )
            if not harm_subcategory:
                st.stop()

submitted = st.button("Submit your answers", type="primary", use_container_width=True)
if submitted:
    current_datetime = datetime.datetime.now()
    st.write(current_datetime)
    st.balloons()
