from typing import Any
import streamlit as st

TTL = 30 * 60


def display_question(
    *,
    question: str,
    widget_cls: Any,
    key_prefix: str = "",
    widget_kwargs: dict = None,
    description: str = None,
    container: st.delta_generator.DeltaGenerator = None,
    help_text=None,
    show_descriptions=True,
) -> list | str:
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


def stop_condition(condition: bool, submit_message: str) -> None:
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
        self.stakeholders = None

    @st.cache_data(
        ttl=TTL, show_spinner="Reading the annotators' list from Google Sheets..."
    )
    def download(_self, _conn) -> None:
        df_stakeholders = (
            _conn.read(
                worksheet="Stakeholders",
                ttl=0,
                usecols=[0, 1],
            )
            .dropna(how="all", axis=0)
            .dropna(how="all", axis=1)
        )
        _self.stakeholders = {
            d["Stakeholder"]: d["Definition"]
            for d in df_stakeholders.to_dict(orient="records")
        }
        return _self

    def description(self) -> str:
        stakeholders_description = ""
        for k, v in self.stakeholders.items():
            stakeholders_description += f"- **{k}**: {v}\n"
        return stakeholders_description

    def values(self) -> list:
        return self.stakeholders.keys()


class Harms:
    def __init__(self) -> None:
        self.harm_descriptions = None
        self.harm_categories = None

    @st.cache_data(
        ttl=TTL, show_spinner="Reading the AI harm taxonomy from Google Sheets..."
    )
    def download(_self, _conn):
        try:
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
        except Exception as e:
            st.error("Cannot connect to Google Sheets. Error: " + str(e))
            st.info(
                "Try to refresh the page. If the problem persists please inform us via Slack."
            )
            st.stop()

        _self.harm_categories = {
            col_name: series.dropna().to_list() for col_name, series in df_harms.items()
        }
        _self.harm_descriptions = df_harm_descriptions.set_index("Harm").squeeze()
        return _self

    def values(self, category=None) -> list:
        if category is None:
            return list(self.harm_categories.keys()) + ["Other"]
        else:
            return self.harm_categories[category]

    def description(self, category=None) -> str:
        if category == "type":
            harm_type_help_text = """
            - **Actual harm**: _a negative impact recorded as having occurred_ in media reports, research papers, legal dockets, assessments/audits, etc, regarding or mentioning an incident (see below). Ideally, an actual harm will have been corroborated through public statements by the deployer or developer of the technology system, though this is not always the case.
            - **Potential harm**: _a negative impact mentioned as being possible or likely but which is not recorded as having occurred_ in media reports, research papers, etc. A potential harm is sometimes referred to as a ‘risk’ or ‘hazard’ by journalists, risk managers, and others.
            """
            return harm_type_help_text

        harm_categories_description = ""
        if category is None:
            subset_harm_categories = self.harm_descriptions.loc[
                self.harm_categories.keys()
            ].to_dict()
        else:
            subset_harm_categories = self.harm_descriptions.loc[
                self.harm_categories[category]
            ].to_dict()
        for k, v in subset_harm_categories.items():
            harm_categories_description += f"- **{k}**: {v}\n"
        return harm_categories_description

    def mindmap(self) -> str:
        taxonomy_mindmap = """
---
markmap:
    colorFreezeLevel: 2
---
# AI Harm Taxonomy
"""

        for k, v in self.harm_categories.items():
            taxonomy_mindmap += f"## {k}\n"
            for i in v:
                taxonomy_mindmap += f"### {i}\n"
        return taxonomy_mindmap
