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
import shelve
import ollama
import json
import os.path

WORD_LIMIT = 8000 * 70 / 100
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

with st.sidebar:
    if st.button("Clear cache", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


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

repository.to_csv("repository.csv")
selected_llm = build_llm_selection()

# with shelve.open("incident_media", "c") as db_media:
#     for k in incidents_list:
#         if k in db_media:
#             with open(f"media/{k}.txt", "w") as f:
#                 json.dump(db_media.get(k), f)
# with shelve.open("incident_summaries", "c") as db_summaries:
#     for k in incidents_list:
#         if k in db_summaries:
#             with open(f"summaries/{k}.txt", "w") as f:
#                 json.dump(db_summaries.get(k), f)

prompt_template = """Act like an excellent journalist and writer.
You have a particularly good expertise in writing dense articles summaries.
Below is a media article of an AI incident:

(start of the media article)
{0}
(end of the media article)

Based on the above article, generate a summary of the incident, including the following information:

- A clear and concise description of the incident.
- The stakeholders impacted by the incident and their roles.
- The specific harm caused to the stakeholders.
- The potential consequences of the incident.

Keep the summary concise, with no title, and dive straight into the topic.
"""
if st.sidebar.button("Generate summaries", use_container_width=True):
    progress = st.progress(0.0, text="Summarizing incidents")

    # current = st.empty()
    for i, incident_id in enumerate(incidents_list, 1):
        # with st.expander(repository.loc[incident_id, "title"], expanded=False):
        progress.progress(
            i / len(incidents_list),
            text=f"Summarizing incidents: {incident_id} ({i}/{len(incidents_list)})",
        )

        # summary_tab, media_tab = st.tabs(["Summary", "Media"])
        incident_page = repository.loc[incident_id, "links"]

        media_descriptions = None
        if os.path.exists(f"media/{incident_id}.txt"):
            try:
                with open(f"media/{incident_id}.txt", "r") as f:
                    media_descriptions = json.load(f)
            except:
                pass
        if media_descriptions is None:
            if not incident_page:
                st.error(f"No link for `{incident_id}`")
                continue
            try:
                links_list = get_list_of_links(incident_page)
            except:
                st.error(f"No links for `{incident_id}` ({incident_page})")
                continue

            media_descriptions = extract_content(links_list, WORD_LIMIT)
            if not media_descriptions:
                st.error(f"No content for `{incident_id}` ({incident_page})")
                st.markdown("\n".join(links_list))
                continue

            with open(f"media/{incident_id}.txt", "w") as f:
                json.dump(media_descriptions, f)

        # tabs = media_tab.tabs(
        #     [f"Link {n}" for n in range(1, len(media_descriptions) + 1)]
        # )
        # for result, tab in zip(media_descriptions, tabs):
        #     tab.markdown(result)
        if os.path.exists(f"summaries/{incident_id}.txt"):
            continue

        summary = ollama.generate(
            model=selected_llm,
            prompt=prompt_template.format(media_descriptions[0]),
        )["response"]

        with open(f"summaries/{incident_id}.txt", "w") as f:
            json.dump(summary, f)


if not incident:
    st.stop()

incident_page = repository.loc[incident, "links"]
st.markdown("##### Incident: " + repository.loc[incident, "title"])

st.page_link(
    incident_page,
    label="Go to the incident page",
    use_container_width=True,
    icon="🌐",
)
with st.container(height=200, border=False):
    st.info(scrap_incident_description(incident_page))

links_list = get_list_of_links(incident_page)

if not links_list:
    st.error("Empty list of links")
    st.stop()
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


(questions_tab, summaries_tab) = st.tabs(["Taxonomy questions", "All summaries"])

if st.sidebar.button("LLM run", use_container_width=True, type="primary"):
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
