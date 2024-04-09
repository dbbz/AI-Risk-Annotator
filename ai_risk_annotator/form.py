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
        self.stakeholders = None

    @st.cache_data(
        ttl=TTL, show_spinner="Reading the annotators' list from Google Sheets..."
    )
    def download(self, _conn) -> None:
        df_stakeholders = (
            _conn.read(
                worksheet="Stakeholders",
                ttl=0,
                usecols=[0, 1],
            )
            .dropna(how="all", axis=0)
            .dropna(how="all", axis=1)
        )
        self.stakeholders = {
            d["Stakeholder"]: d["Definition"]
            for d in df_stakeholders.to_dict(orient="records")
        }
        return self

    def description(self) -> str:
        stakeholders_description = ""
        for k, v in self.stakeholders.items():
            stakeholders_description += f"- **{k}**: {v}\n"
        return stakeholders_description


class HarmCategories:
    def __init__(self) -> None:
        self.harm_descriptions = None
        self.harm_categories = None

    @st.cache_data(
        ttl=TTL, show_spinner="Reading the AI harm taxonomy from Google Sheets..."
    )
    def download(self, _conn):
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

        self.harm_categories = {
            col_name: series.dropna().to_list() for col_name, series in df_harms.items()
        }
        self.harm_descriptions = df_harm_descriptions.set_index("Harm").squeeze()
        return self

    def description(self) -> str:
        harm_categories_description = ""
        subset_harm_categories = self.harm_descriptions.loc[
            self.harm_categories.keys()
        ].to_dict()
        for k, v in subset_harm_categories.items():
            harm_categories_description += f"- **{k}**: {v}\n"
        return harm_categories_description


class HarmSubcategory:
    def __init__(self) -> None:
        self.harm_descriptions = None
        self.harm_categories = None
        self.harm_category = None

    def description(self) -> str:
        harm_subcategories_description = ""
        subset_harm_subcategories = self.harm_descriptions.loc[
            self.harm_categories[self.harm_category]
        ].to_dict()
        for k, v in subset_harm_subcategories.items():
            harm_subcategories_description += f"- **{k}**: {v}\n"
        return harm_subcategories_description


class HarmType:
    def description(self) -> str:
        harm_type_help_text = """
        - **Actual harm**: _a negative impact recorded as having occurred_ in media reports, research papers, legal dockets, assessments/audits, etc, regarding or mentioning an incident (see below). Ideally, an actual harm will have been corroborated through public statements by the deployer or developer of the technology system, though this is not always the case.
        - **Potential harm**: _a negative impact mentioned as being possible or likely but which is not recorded as having occurred_ in media reports, research papers, etc. A potential harm is sometimes referred to as a ‘risk’ or ‘hazard’ by journalists, risk managers, and others.
        """
        return harm_type_help_text
