import hmac
import pickle
import re

import html2text
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from markdownify import markdownify

TTL = 30 * 60


def create_side_menu():
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
    with st.sidebar:
        st.markdown("# AI and Algorithmic Harm Annotator")
        st.divider()
        st.page_link("app.py", label="Instructions", icon="📖")
        st.page_link("pages/annotator.py", label="Annotator", icon="✍🏻")
        st.page_link("pages/results.py", label="Results", icon="📈")

        if "debug_mode" in st.secrets and st.secrets["debug_mode"]:
            st.page_link("pages/automatic.py", label="LLM", icon="🦜")


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

    if "debug_mode" in st.secrets and st.secrets["debug_mode"]:
        return True

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


# Load the incidents descriptions and related links
# scrapped from the AIAAIC website as they are not in the sheet
@st.cache_data(ttl=TTL)
def load_extra_data():
    with open("descriptions.pickle", "rb") as f:
        descriptions = pickle.load(f)
    with open("links.pickle", "rb") as f:
        links = pickle.load(f)

    return descriptions, links


def download_public_sheet_as_csv(csv_url, filename="downloaded_sheet.csv"):
    """Downloads a public Google Sheet as a CSV file.

    Args:
        csv_url (str): The CSV download URL of the Google Sheet.
        filename (str, optional): The filename for the downloaded CSV file. Defaults to "downloaded_sheet.csv".
    """

    try:
        response = requests.get(csv_url)
        response.raise_for_status()  # Check for HTTP errors

        with open(filename, "wb") as f:
            f.write(response.content)

    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")


# Load the actual AIAAIC repository (list of incidents)
# It used to be downloaded from the online repo
# but due to frequent changes in the sheet format
# I ended up using an offline (potentially not up to date) version
@st.cache_data(ttl=TTL)
def read_incidents_repository_from_file():
    download_public_sheet_as_csv(
        "https://docs.google.com/spreadsheets/d/1Bn55B4xz21-_Rgdr8BBb2lt0n_4rzLGxFADMlVW0PYI/export?format=csv&gid=888071280"
    )
    df = (
        pd.read_csv("downloaded_sheet.csv", skip_blank_lines=True, skiprows=[0, 2])
        .dropna(how="all")
        .dropna(axis=1, how="all")
    )

    df = df.set_index(df.columns[0]).rename(columns=lambda x: x.strip())[
        ["Headline", "Description/links"]
    ]

    df.columns = ["title", "links"]
    return df


@st.cache_data(ttl=TTL)
def download_incidents_repository():
    AIAAIC_SHEET_ID = "1Bn55B4xz21-_Rgdr8BBb2lt0n_4rzLGxFADMlVW0PYI"
    AIAAIC_SHEET_NAME = "Repository"

    url = f"https://docs.google.com/spreadsheets/d/{AIAAIC_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={AIAAIC_SHEET_NAME}"
    df = (
        pd.read_csv(url, skip_blank_lines=True)
        .dropna(how="all")
        .dropna(axis=1, how="all")
    )

    df = df.set_index(df.columns[0]).rename(columns=lambda x: x.strip())[
        ["Headline/title", "Description/links"]
    ]

    df.columns = ["title", "links"]
    return df


@st.cache_data(ttl=TTL, show_spinner="Fetching more information about the incident...")
def scrap_incident_description(link):
    soup = BeautifulSoup(requests.get(link).text, "html.parser")

    # This is dangeriously hard-coded.
    description = soup.find_all(
        # class_="hJDwNd-AhqUyc-uQSCkd Ft7HRd-AhqUyc-uQSCkd purZT-AhqUyc-II5mzb ZcASvf-AhqUyc-II5mzb pSzOP-AhqUyc-qWD73c Ktthjf-AhqUyc-qWD73c JNdkSc SQVYQc"
        class_="hJDwNd-AhqUyc-uQSCkd Ft7HRd-AhqUyc-uQSCkd jXK9ad D2fZ2 zu5uec OjCsFc dmUFtb wHaque g5GTcb"
    )

    header_pattern = r"^(#+)\s+(.*)"
    description = markdownify("\n".join((str(i) for i in description[1:-1])))
    description = re.sub(header_pattern, r"#### \2", description)

    description = description.replace(
        "](/aiaaic-repository",
        "](https://www.aiaaic.org/aiaaic-repository",
    ).replace("### ", "##### ")
    return description


def get_deepest_text(tag):
    if tag.string:
        return tag.string.strip()  # Return text if it's a text node

    # Recursive search for text within children
    for child in tag.children:
        text = get_deepest_text(child)
        if text:
            return text

    return None


@st.cache_data(ttl=TTL, show_spinner="Fetching the list of links on the incident...")
def get_list_of_media_links(page_url):
    soup = BeautifulSoup(requests.get(page_url).text, "html.parser")
    section = soup.find(string=re.compile(", commentar"))
    if not section:
        section = soup.find(string=re.compile("act check 🚩"))
    if section:
        li_list = section.find_next("ul").find_all("li")
        results = markdownify("\n".join(str(i) for i in li_list))
        # links = [get_deepest_text(li) for li in li_list]
        return results
    else:
        return ""


# The list of annotators (or the initials thereof)
@st.cache_data(
    ttl=TTL, show_spinner="Reading the annotators' list from Google Sheets..."
)
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


@st.cache_data(
    ttl=TTL, show_spinner="Reading the annotators' list from Google Sheets..."
)
def get_stakeholders(_conn):
    df_stakeholders = (
        _conn.read(
            worksheet="Stakeholders",
            ttl=0,
            usecols=[0, 1],
        )
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    return {
        d["Stakeholder"]: d["Definition"]
        for d in df_stakeholders.to_dict(orient="records")
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


@st.cache_data(
    ttl=TTL, show_spinner="Reading the AI harm taxonomy from Google Sheets..."
)
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


@st.cache_data(
    ttl=TTL, show_spinner="Reading the incidents short-list from Google Sheets..."
)
def get_incidents_list(_conn):
    df_shortlist = (
        _conn.read(worksheet="Batches", ttl=0)
        .dropna(how="all", axis=0)
        .dropna(how="all", axis=1)
    )
    df_shortlist = df_shortlist.iloc[:, -1].apply(lambda x: str(x).strip())
    return df_shortlist.to_list()


@st.cache_data(
    ttl=TTL, show_spinner="Reading the old annotations from Google Sheets..."
)
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


@st.cache_data(ttl=TTL, show_spinner="Fetching the list of links on the incident...")
def get_list_of_links(page_url):
    soup = BeautifulSoup(requests.get(page_url).text, "html.parser")
    section = soup.find(string=re.compile(", commentar"))

    if not section:
        section = soup.find(string=re.compile("act check 🚩"))
    if section:
        li_list = section.find_next("ul").find_all("li")
        # results = markdownify("\n".join(str(i) for i in li_list))
        results = [html2text.html2text(str(i)) for i in li_list]

        pattern = r"\[([^][]*)\]\(([^()]*)\)"
        urls = []
        for link in results:
            match = re.search(pattern, link)
            if match:
                urls.append(match.group(2))

        # links = [get_deepest_text(li) for li in li_list]
        return urls
    else:
        return []
