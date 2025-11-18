import polars as pl
import streamlit as st
from PIL import Image

from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.trello import tr_api
from enviroflow_app.st_components.st_logger import Log_Level, st_logger


def setup_streamlit_page(title: str | None = None) -> None:
    """Configures streamlit app with page title, wide layout and favicon"""
    if title is None:
        title = "Enviroflow App"
    favicon = Image.open("favicon.png")
    st.set_page_config(
        page_title=title,
        layout="wide",
        page_icon=favicon,
    )


def init_session_state_key(key_to_insert: str) -> None:
    if key_to_insert not in st.session_state:
        st_logger(
            Log_Level.INFO,
            f"📦️ initialising key:{key_to_insert} in session state",
        )
        st.session_state[key_to_insert] = None


def add_object_to_session_state(key_to_insert: str, obj: object) -> None:
    if key_to_insert not in st.session_state:
        st_logger(
            Log_Level.INFO,
            f"📦️ initialising key:{key_to_insert} in session state",
        )
        st.session_state[key_to_insert] = obj


def set_session_keys(session_state_keys: list[str] | str) -> None:
    """Checks the list of session state keys the page needs,
    initialises it if it isn't alreadyin the session states dict.
    """
    if isinstance(session_state_keys, str):
        init_session_state_key(session_state_keys)

    elif isinstance(session_state_keys, list):
        for key in session_state_keys:
            init_session_state_key(key)


def init_default_session() -> None:
    """Checks streamlit's session keys and initiates the  the default session"""
    with st.spinner("💡initializing session"):
        set_session_keys(["dev", "db_conn", "table_list", "tr_conn"])
        if st.session_state["db_conn"] is None:
            duck_token = st.secrets["motherduck"]["token"]
            st_logger(Log_Level.INFO, "📼 connecting to database")
            dd_conn = md.MotherDuck(duck_token, "enviroflow")
            st_logger(Log_Level.INFO, "👍 connected to database")
            st.session_state["db_conn"] = dd_conn

        if st.session_state["tr_conn"] is None:
            st_logger(Log_Level.INFO, "🗃️ connecting to Trello")
            TR_CONN = tr_api.TrCreds(
                api_key=st.secrets["trello"]["api_key"],
                api_token=st.secrets["trello"]["api_token"],
            )
            st_logger(Log_Level.INFO, "👍 connected to Trello")
            st.session_state["tr_conn"] = TR_CONN

        if st.session_state["dev"] is None:
            st.session_state["dev"] = False


def save_table_to_ss(table_name: str, update_table: pl.DataFrame | None = None) -> None:
    if table_name not in st.session_state:
        set_session_keys(session_state_keys=table_name)
    if update_table is not None:
        st.session_state[table_name] = update_table
        st_logger(Log_Level.INFO, f"📦️ updated {table_name} in session state")
    elif st.session_state[table_name] is None:
        st_logger(Log_Level.INFO, f"📦️ fetching {table_name} table")
        # assumes the db connection is live in the session state
        fetched_table = st.session_state["db_conn"].get_table(table_name=table_name)
        st.session_state[table_name] = fetched_table
        st_logger(Log_Level.INFO, f"📦️ saved {table_name} to session state")
    else:
        st_logger(
            Log_Level.INFO,
            f"skiping {table_name} which is loaded in session state",
        )


def load_md_data_to_session_state(tables: str | list[str]) -> None:
    """Loads database tables from motherduck to the session state.
    expects a list of names that should match the dataa
    """
    if isinstance(tables, str):
        save_table_to_ss(tables)
    elif isinstance(tables, list):
        for table_name in tables:
            save_table_to_ss(table_name)


def debug_toggle() -> None:
    with st.sidebar:
        st.toggle("toggle Dev Mode", key="dev")
    if st.session_state.dev:
        st.write(st.session_state)
