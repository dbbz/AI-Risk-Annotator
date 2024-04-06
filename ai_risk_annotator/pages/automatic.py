import streamlit as st
from llm import build_llm_selection, extract_content, call_ollama_chat
from utils import (
    check_password,
    create_side_menu,
    read_incidents_repository_from_file,
    stakeholders,
    get_list_of_links,
    scrap_incident_description,
)

WORD_LIMIT = 128_000 * 70 / 100
st.set_page_config(page_title="AI Harm Annotator", layout="wide")
create_side_menu()
st.markdown("# LLM-based annotation")


def clear_history():
    st.session_state["chat_history"] = {}


# Put the chat history in a session state
if "chat_history" not in st.session_state or st.sidebar.button(
    "Clear history",
    use_container_width=True,
    type="secondary",
    key="clear_history",
):
    clear_history()


# Read the incident repo and make the dropdown menu
repository = read_incidents_repository_from_file()
incidents_list = sorted(list(repository.index), reverse=True)
incident = st.selectbox(
    "incident",
    options=incidents_list,
    index=None,
    label_visibility="collapsed",
    on_change=clear_history,
)

selected_llm = build_llm_selection()


if not incident:
    st.stop()

incident_page = repository.loc[incident, "links"]
st.markdown("##### Incident: " + repository.loc[incident, "title"])
with st.container(height=200, border=False):
    st.info(scrap_incident_description(incident_page))

links_list = get_list_of_links(incident_page)
media_descriptions = extract_content(links_list, WORD_LIMIT)

with st.sidebar:
    st.divider()
    selected_media_link = st.selectbox(
        "Media article to provide as context", range(1, len(media_descriptions) + 1)
    )
selected_media_link -= 1

# st.sidebar.write(st.session_state.chat_history)

with st.expander("Media articles", expanded=False):
    tabs = st.tabs([f"Link {n}" for n in range(1, len(media_descriptions) + 1)])
    for result, tab in zip(media_descriptions, tabs):
        tab.markdown(result)
prompt_template = f"""
You are an outstanding AI expert, specialized in AI incidents.
You are tasked with annotating AI incidents following a precise harm taxonomy.
Below is a media article covering an incident related to AI.
I want you to carefully answer my following questions based on the incident description in the article.
Do not make things up. If you do not know, simply say that do you do not know.

Here is the media article:
{media_descriptions[selected_media_link]}


"""

if selected_llm not in st.session_state["chat_history"]:
    st.session_state.chat_history[selected_llm] = []


(questions_tab,) = st.tabs(["Taxonomy questions"])

# if st.sidebar.button(
#     "Summarize the incident", use_container_width=True, type="primary"
# ):
with questions_tab:
    st.chat_message("user").write("Summarize the incident")
    st.session_state.chat_history[selected_llm].append(
        {"role": "user", "content": prompt_template, "show": False}
    )

    prompt_template = f"""
    Based on this article, make a short summary of the incident emphasizing who was harmed and how they were harmed.
    """

    call_ollama_chat(selected_llm, prompt_template, store_prompt=False)

# if st.sidebar.button(
#     "Who are the impacted stakeholders?", use_container_width=True, type="primary"
# ):
with questions_tab:
    st.chat_message("user").write("Who are the impacted stakeholders?")

    stakeholders_descriptions = ""
    for k, v in stakeholders.items():
        stakeholders_descriptions += f"- **{k}**: {v}\n"

    # prompt_template = f"""Let us first define the possible stakeholders we are interested in.
    # These could be one or many of: {", ".join(stakeholders.keys())}.
    # Based on the aforementioned list of impacted stakeholders, which ones are relevant to the AI incident in the media article above?
    # Give a short answer and simply list the impacted stakeholders without explanations.
    # """

    prompt_template = f"""We have established the following stakeholders taxonomy:
    {stakeholders_descriptions}.
    Based on the description of the AI incident and the stakeholders taxonomy, determine which stakeholders are impacted in the case of this incident?
    Keep your answer short.
    """

    call_ollama_chat(selected_llm, prompt_template, store_prompt=False)

# with discussion_tab:
#     prompt = st.chat_input(max_chars=4096 * 3)
#     for message in st.session_state.chat_history[selected_llm]:
#         if message.get("show", True):
#             st.chat_message(message["role"]).write(message["content"])

#     if prompt:
#         call_ollama_chat(selected_llm, prompt)
