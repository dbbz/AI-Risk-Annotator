import streamlit as st


def display_question(
    incident_id,
    question,
    description,
    widget_cls,
    widget_kwargs,
    container=None,
    help_text=None,
    show_descriptions=True,
):
    container = container or st.container(border=False)
    with container:
        st.markdown(
            question,
            help=help_text,
        )
        if show_descriptions and description is not None:
            st.caption(description)

        result = widget_cls(
            question,
            label_visibility="collapsed",
            key=f"{incident_id}__{question}",
            **widget_kwargs,
        )
    return result
