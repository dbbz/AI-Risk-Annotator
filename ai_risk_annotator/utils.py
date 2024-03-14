import hmac

import streamlit as st
from streamlit_gsheets import GSheetsConnection


def create_side_menu():
    with st.sidebar:
        st.markdown("# AI and Algorithmic Harm Annotator")
        st.divider()
        st.page_link("app.py", label="Instructions", icon="📖")
        st.page_link("pages/annotator.py", label="Annotator", icon="✍🏻")
        st.page_link("pages/results.py", label="Results", icon="📈")


def switch_page(page_name: str):
    """
    Switch page programmatically in a multipage app

    Args:
        page_name (str): Target page name
    """
    from streamlit.runtime.scriptrunner import RerunData, RerunException
    from streamlit.source_util import get_pages

    def standardize_name(name: str) -> str:
        return name.lower().replace("_", " ")

    page_name = standardize_name(page_name)

    pages = get_pages("streamlit_app.py")  # OR whatever your main page is called

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )

    page_names = [standardize_name(config["page_name"]) for config in pages.values()]

    raise ValueError(f"Could not find page {page_name}. Must be one of {page_names}")


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


columns = [
    "datetime",
    "annotator",
    "incident_ID",
    "stakeholders",
    "harm_category",
    "harm_subcategory",
    "harm_type",
    "notes",
    "timestamp",
]


# The list of annotators (or the initials thereof)
@st.cache_data
def get_annotators():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error("Cannot connect to Google Sheet. Error: " + str(e))
        annotators = [
            "CP",
            "DB",
            "EP",
            "JH",
            "GA",
            "HP",
            "JK",
            "LW",
            "MS",
            "PG",
            "PN",
            "TC",
            "TD",
            "US",
        ]
    else:
        with st.spinner("Reading from Google Sheet..."):
            df_annotators = (
                conn.read(
                    worksheet="Annotators",
                    ttl=0,
                    usecols=[0],
                )
                .dropna(how="all", axis=0)
                .dropna(how="all", axis=1)
            )
            annotators = df_annotators["Annotators"].to_list()
    return annotators


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


harm_categories_descriptions = {
    "Autonomy": {
        "description": "Loss of or restrictions to the ability or rights of an individual, group or entity to make decisions and control their identity",
        "subcategories": [],
    },
    "Physical": {
        "description": "Physical injury to an individual or group, or damage to physical property",
        "subcategories": [],
    },
    "Emotional & psychological": {
        "description": "Direct or indirect impairment of the emotional and psychological mental health of an individual, organisation, or society",
        "subcategories": [],
    },
    "Reputational": {
        "description": "Damage to the reputation of an individual, group or organisation ",
        "subcategories": [],
    },
    "Financial & business": {
        "description": "Use or misuse of a technology system in a manner that damages the financial interests of an individual or group, or which causes strategic, operational, legal or financial harm to a business or other organisation",
        "subcategories": [],
    },
    "Human rights & civil liberties": {
        "description": "Use or misuse of a technology system in a manner that compromises fundamental human rights and freedoms",
        "subcategories": [],
    },
    "Societal & cultural": {
        "description": "Harms affecting the functioning of societies, communities and economies caused directly or indirectly by the use or misuse technology systems",
        "subcategories": [],
    },
    "Political & economic": {
        "description": "Manipulation of political beliefs, damage to political institutions and the effective delivery of government services",
        "subcategories": [],
    },
    "Environmental": {
        "description": "Damage to the environment directly or indirectly caused by a technology system or set of systems",
        "subcategories": [],
    },
    # "Other": {"description": "", "subcategories": []},
}
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
