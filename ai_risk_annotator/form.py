import streamlit as st


TTL = 30 * 60


def display_question(
    *,
    question,
    widget_cls,
    key_prefix="",
    widget_kwargs=None,
    description=None,
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

        # below is a trick to prevent streamlit from deleting previous answers
        # had they disappeared from the screen temporarily
        key = f"{key_prefix}__{question}"

        if key in st.session_state:
            st.session_state[key] = st.session_state[key]

        widget_kwargs = widget_kwargs or {}
        result = widget_cls(
            question,
            label_visibility="collapsed",
            key=key,
            **widget_kwargs,
        )
    return result


def stop_condition(condition, submit_message):
    if condition:
        st.button(
            submit_message,
            type="primary",
            use_container_width=True,
            disabled=True,
        )
        st.stop()


class Stakeholders:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        pass

    @st.cache_data(
        ttl=TTL, show_spinner="Reading the annotators' list from Google Sheets..."
    )
    def download(self, _conn):
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
