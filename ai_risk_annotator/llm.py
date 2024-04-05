import ollama
import pandas as pd
import streamlit as st
from trafilatura import extract, fetch_url


def build_llm_selection():
    try:
        models_info = get_available_local_llms()
    except Exception as e:
        st.error(
            "Cannot connect to your local LLM. Please check that Ollama is running in the background"
        )
        st.stop()
    available_llms = models_info.LLM.to_list()

    # If the retrieved list of LLMs is empty
    if not available_llms:
        st.info(
            "There are no installed LLMs locally. Please refer to the Ollama documentation to install one."
        )
        st.stop()

    # Select which LLMs to play with
    with st.sidebar.container(border=True):
        st.subheader("Available local LLMs")
        selected_llm = st.selectbox(
            "Choose an LLM",
            available_llms,
            index=available_llms.index("phi:latest"),
            label_visibility="collapsed",
            key="selected_llm",
        )
    return selected_llm


def get_available_local_llms():
    return (
        pd.json_normalize(ollama.list()["models"])
        .drop(
            [
                "digest",
                "details.format",
                "details.families",
                "details.parent_model",
                "modified_at",
                "model",
            ],
            axis=1,
        )
        .rename(
            columns={
                "name": "LLM",
                "size": "Size",
                "details.family": "Family",
                "details.parameter_size": "Parameters",
                "details.quantization_level": "Quantization",
            },
        )
    )


def stream_chat(model, messages):
    response_generator = (
        chunk["message"]["content"]
        for chunk in ollama.chat(
            model=model,
            messages=messages,
            stream=True,
        )
    )
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator)
        # response += r

    return response


@st.cache_data(ttl=3600, show_spinner="Parsing the web page...")
def extract_content(links_list, WORD_LIMIT):
    pages = [fetch_url(link) for link in links_list]
    results = [extract(page, include_comments=False) for page in pages]
    results = [
        result for result in results if result is not None and len(result) <= WORD_LIMIT
    ]
    results = sorted(results, reverse=True, key=lambda x: len(x))

    return results
