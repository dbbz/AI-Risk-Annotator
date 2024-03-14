import streamlit as st
from streamlit_markmap import markmap
import streamlit.components.v1 as components

st.set_page_config(page_title="AI and Algorithmic Harm Annotator", layout="centered")

st.sidebar.page_link("app.py", label="Annotator", icon="✍🏻")
st.sidebar.page_link("pages/instructions.py", label="Instructions", icon="📖")
# st.sidebar.page_link("pages/analysis.py", label="Results", icon="📈")

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

st.markdown("# 👋🏼")
st.markdown("""### Welcome to the AIAAIC's Harms Taxonomy project""")
st.markdown("""
    #### Definitions
    Bear in mind the following terms when annotating incidents/issues:
    - _Actual harm_ - **a negative impact recorded as having occurred** in media reports, research papers, legal dockets, assessments/audits, etc, regarding or mentioning an incident (see below). Ideally, an actual harm will have been corroborated through public statements by the deployer or developer of the technology system, though this is not always the case.
    - _Potential harm_ - **a negative impact mentioned as being possible or likely but which is not recorded as having occurred** in media reports, research papers, etc. A potential harm is sometimes referred to as a ‘risk’ or ‘hazard’ by journalists, risk managers, and others.
    - _Stakeholder_ - **external** (ie. not deployers or developers) individuals, groups, communities or entities using, being targeted by, or otherwise directly or indirectly negatively affected by a technology system.

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

st.link_button(
    "Stakeholders definitions",
    "https://docs.google.com/document/d/1QxXMWA9na4Sf3hQpQXYI2vBtRIpP8hOE7S_3MDck0N4/edit",
)
st.link_button(
    "Stakeholders definitions",
    "https://docs.google.com/document/d/1pQjNyAbvtelHqrN6Rz4TlixOak6eSJzkKUAGN30V8bo/edit",
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

st.markdown("#### Instruction slides")
components.iframe(
    "https://slides.com/db-5/ai-harm-taxonomy/embed",
    width=576,
    height=420,
    scrolling=False,
)

st.markdown("#### Harms taxonomy overview")
markmap(taxonomy_mindmap)
