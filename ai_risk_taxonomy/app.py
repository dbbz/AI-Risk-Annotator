import streamlit as st
import pandas as pd
import shelve
from streamlit_gsheets import GSheetsConnection
import datetime
import hmac

# The list of annotators (or the initials thereof)
annotators = ["CP", "DB", "EP", "JH", "GA", "HP", "LW", "MS", "PN", "TC", "TD", "US"]

# The list of harm categories and sub-categories
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

# The list of impacted stakeholders
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

# Make a string containing the stakeholders descriptions
stakeholders_help_text = ""
for k, v in stakeholders.items():
    stakeholders_help_text += f"- **{k}**: {v}\n"


# Load the incidents descriptions and related links
# scrapped from the AIAAIC website as they are not in the sheet
@st.cache_data
def load_extra_data():
    with shelve.open("description", "r") as db:
        descriptions = dict(db)
    with shelve.open("links", "r") as db:
        links = dict(db)

    return descriptions, links


# Load the actual AIAAIC repository (list of incidents)
# It used to be downloaded from the online repo
# but due to frequent changes in the sheet format
# I ended up using an offline (potentially not up to date) version
@st.cache_data
def load_incidents_repository():
    df = pd.read_csv("repository.csv").dropna(how="all")
    df = df.set_index(df.columns[0])[["Headline/title", "Description/links"]]
    df.columns = ["title", "links"]
    return df


# Password protect to avoid annotation vandalism
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


if not check_password():
    st.stop()  # Do not continue if check_password is not True.


st.title("AI Risk Taxonomy")
with st.expander("📖 Instructions"):
    st.markdown("""
    👋🏼  Thank you for taking part in the AI Risk Taxonomy project.

    - Instruction 1
    - Instruction 2
    - ...
    """)

# Connect to the Google Sheet where to store the answers
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Cannot connect to Google Sheet. Error: " + str(e))


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
        key=incident + "__impacted",
    )
    if not impacted_stakeholder:
        st.stop()

results = {}
for stakeholder in impacted_stakeholder:
    results[stakeholder] = {}
    with st.container(border=True):
        st.markdown(
            f"What :violet[category] of harm impacts `{stakeholder}`? *(multiple options are possible)*",
            help="Stated actual negative impact(s) of incident/issue",
        )
        harm_category = st.multiselect(
            "harm_category",
            harm_categories.keys(),
            default=None,
            label_visibility="collapsed",
            key=f"{incident}__{stakeholder}__harm_category",
        )
        if not harm_category:
            st.stop()

        for harm_cat in harm_category:
            st.markdown(
                f"What :orange[specific] `{harm_cat}` harm impacts `{stakeholder}`? *(multiple options are possible)*",
                help="Stated specific negative impact(s) of incident/issue",
            )
            harm_subcategory = st.multiselect(
                "harm_subcategory",
                harm_categories[harm_cat],
                default=None,
                label_visibility="collapsed",
                key=f"{incident}__{stakeholder}__{harm_cat}__harm_subcategory",
            )
            if not harm_subcategory:
                st.stop()
            results[stakeholder][harm_cat] = harm_subcategory

submitted = st.button("Submit your answers", type="primary", use_container_width=True)
if submitted:
    # current_datetime = datetime.datetime.now()
    current_datetime = datetime.date.today()
    timestamp = int(datetime.datetime.now().timestamp())
    tabular_results = []
    for stakeholder, harm in results.items():
        for harm_cat, harm_subcat_list in harm.items():
            for harm_subcat in harm_subcat_list:
                tabular_results.append(
                    [
                        current_datetime,
                        user,
                        incident,
                        stakeholder,
                        harm_cat,
                        harm_subcat,
                        timestamp,
                    ]
                )

    columns = [
        "datatime",
        "annotator",
        "incident_ID",
        "stakeholders",
        "harm_category",
        "harm_subcategory",
        "timestamp",
    ]
    df_update = pd.DataFrame(data=tabular_results, columns=columns)

    with st.spinner("Writing to Google Sheet..."):
        df = conn.read(worksheet="Annotations", ttl=0, usecols=columns).dropna()
        df = pd.concat([df, df_update], ignore_index=True)
        conn.update(worksheet="Annotations", data=df)

    st.balloons()
    st.toast("Your answers were submitted.")
    st.toast("You can select another incident to annotate.")

    # Clear cache?
