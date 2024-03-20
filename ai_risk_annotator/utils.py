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
@st.cache_data(show_spinner="Reading the annotators' list from Google Sheets...")
def get_annotators(_conn):
    df_annotators = (
        _conn.read(
            worksheet="Annotators",
            ttl=0,
            usecols=[0],
        )
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    return df_annotators["Annotators"].to_list()


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


@st.cache_data(show_spinner="Reading the AI harm taxonomy from Google Sheets...")
def get_harm_descriptions(_conn):
    df_harms = (
        _conn.read(
            worksheet="Taxonomy",
            ttl=0,
        )
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    df_harm_descriptions = (
        _conn.read(worksheet="Descriptions", ttl=0)
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    return {
        col_name: series.dropna().to_list() for col_name, series in df_harms.items()
    }, df_harm_descriptions.set_index("Harm").squeeze()


@st.cache_data(show_spinner="Reading the incidents short-list from Google Sheets...")
def get_incidents_list(_conn):
    df_shortlist = (
        _conn.read(worksheet="Batches", ttl=0)
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    df_shortlist = df_shortlist.iloc[:, -1].apply(lambda x: x.strip())
    return df_shortlist.to_list()


@st.cache_data(show_spinner="Reading the old annotations from Google Sheets...")
def get_annotated_incidents(_conn):
    df_annotations = (
        (
            _conn.read(worksheet="Annotations", ttl=0)
            .dropna(how="all", axis=0)
            .dropna(how="all", axis=1)
        )[["annotator", "incident_ID"]]
        .groupby("annotator")["incident_ID"]
        .unique()
        .apply(list)
        .to_dict()
    )
    return df_annotations
