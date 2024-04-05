import ollama
import streamlit as st
from llm import build_llm_selection, stream_chat, extract_content
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

# Put the chat history in a session state
if "chat_history" not in st.session_state or st.sidebar.button(
    "Clear history",
    use_container_width=True,
    type="secondary",
    key="clear_history",
):
    st.session_state["chat_history"] = {}

# Read the incident repo and make the dropdown menu
repository = read_incidents_repository_from_file()
incidents_list = sorted(list(repository.index), reverse=True)
incident = st.selectbox(
    "incident",
    options=incidents_list,
    index=None,
    label_visibility="collapsed",
)

selected_llm = build_llm_selection()

if incident:
    incident_page = repository.loc[incident, "links"]
    st.markdown("##### Incident: " + repository.loc[incident, "title"])
    with st.container(height=200, border=False):
        st.info(scrap_incident_description(incident_page))

    links_list = get_list_of_links(incident_page)
    media_descriptions = extract_content(links_list, WORD_LIMIT)
    prompt_template = f"""
You are an outstanding AI expert, specialized in AI incidents.
You are tasked with labelling AI incidents following a precise taxonomy.
Below is a description of an incident related to AI.
I want you to carefully answer my following questions.
Base your answers only on the description I provide.
Do not make things up. If you do not know, simply say it.

Description:
{media_descriptions[0]}

Let's start with the taxonomy of the imapcted stakeholders.
Here are the considered ones: {", ".join(stakeholders.keys())}

"""

    if selected_llm not in st.session_state["chat_history"]:
        st.session_state.chat_history[selected_llm] = []
        st.session_state.chat_history[selected_llm].append(
            {"role": "user", "content": prompt_template}
        )

    # tabs = st.tabs([f"Link {n}" for n in range(1, len(results) + 1)])
    # for result, tab in zip(results, tabs):
    #     tab.code(result, language=None)

    prompt = st.chat_input(max_chars=4096 * 3)

    for message in st.session_state.chat_history[selected_llm]:
        st.chat_message(message["role"]).write(message["content"])
    if prompt:
        st.chat_message("user").write(prompt)
        st.session_state.chat_history[selected_llm].append(
            {"role": "user", "content": prompt}
        )
        try:
            response = stream_chat(
                model=selected_llm,
                messages=st.session_state.chat_history[selected_llm],
            )
            st.session_state.chat_history[selected_llm].append(
                {"role": "assistant", "content": response}
            )
        except ollama.ResponseError as e:
            st.error(
                "Cannot connect to your local LLM. Please check that Ollama is running in the background"
            )
            st.error(e.error)
            if e.status_code == 404:
                with st.spinner("Downloading the model weights..."):
                    ollama.pull(selected_llm)
            else:
                st.stop()
