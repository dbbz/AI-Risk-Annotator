import streamlit as st
import streamlit.components.v1 as components
from streamlit_markmap import markmap
from utils import check_password, create_side_menu, harm_categories

st.set_page_config(page_title="AI and Algorithmic Harm Annotator", layout="centered")


create_side_menu()


st.markdown("# 👋🏼")
st.markdown("""### Welcome to the AIAAIC's Harms Taxonomy project""")
st.divider()
st.markdown("""
    #### Definitions
    Bear in mind the following terms when annotating incidents/issues:
    - _Actual harm_ - **a negative impact recorded as having occurred** in media reports, research papers, legal dockets, assessments/audits, etc, regarding or mentioning an incident (see below). Ideally, an actual harm will have been corroborated through public statements by the deployer or developer of the technology system, though this is not always the case.
    - _Potential harm_ - **a negative impact mentioned as being possible or likely but which is not recorded as having occurred** in media reports, research papers, etc. A potential harm is sometimes referred to as a ‘risk’ or ‘hazard’ by journalists, risk managers, and others.
    - _Stakeholder_ - **external** (ie. not deployers or developers) individuals, groups, communities or entities using, being targeted by, or otherwise directly or indirectly negatively affected by a technology system.
""")
st.divider()
st.markdown("""

    #### Methodology
    Use the following process when annotating incident/issues:
    1. Select your name initials (eg. CP)
    2. Select incident/issue (eg. AIAAIC1372)
    3. Identify and select harmed stakeholder(s)
    4. Identify and select harm category(ies) per stakeholder type
    5. Identify and select harm type(s) per stakeholder type
    6. Record missing, overlapping or unclear harm type names or definitions
    7. Repeat steps 5 & 6 for additional stakeholder types
    """)


st.info(
    "The form is only valid if all the qustions are answered. In case of ambiguity, select the most appropriate answer and use the optional `Notes` field.",
    icon="ℹ️",
)

st.info(
    "Once the Submit button is clicked, please wait until you see the balloons before closing the page.",
    icon="🎈",
)

if not check_password():
    st.stop()

st.page_link(
    "https://docs.google.com/document/d/1QxXMWA9na4Sf3hQpQXYI2vBtRIpP8hOE7S_3MDck0N4/edit",
    label="Stakeholders definitions",
    use_container_width=True,
    icon="🌐",
)
st.page_link(
    "https://docs.google.com/document/d/1pQjNyAbvtelHqrN6Rz4TlixOak6eSJzkKUAGN30V8bo/edit",
    label="Harm definitions",
    use_container_width=True,
    icon="🌐",
)

st.page_link(
    "pages/annotator.py", label="Start annotating", icon="✍🏻", use_container_width=True
)

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

st.divider()

st.markdown("#### Training slides")
components.iframe(
    "https://slides.com/db-5/ai-harm-taxonomy/embed",
    width=576,
    height=420,
    scrolling=False,
)

st.divider()
st.markdown("#### Harms taxonomy overview")
markmap(taxonomy_mindmap)
