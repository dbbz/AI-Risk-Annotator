import streamlit as st


def create_side_menu():
    with st.sidebar:
        st.markdown("# AI and Algorithmic Harm Annotator")
        st.divider()
        st.page_link("app.py", label="Instructions", icon="📖")
        st.page_link("pages/annotator.py", label="Annotator", icon="✍🏻")
        st.page_link("pages/results.py", label="Results", icon="📈")


columns = [
    "datatime",
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
annotators = ["CP", "DB", "EP", "JH", "GA", "HP", "LW", "MS", "PN", "TC", "TD", "US"]

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
