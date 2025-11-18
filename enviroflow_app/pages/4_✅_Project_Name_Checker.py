import polars as pl
import streamlit as st
from loguru import logger

from enviroflow_app import config
from enviroflow_app.elt.motherduck import md
from enviroflow_app.st_components import pre

# TODO, change this to the referencing the databas table

logger.configure(**config.APP_LOG_CONF)
pre.setup_streamlit_page()
pre.init_default_session()
# SESSION_KEYS = ["projects_dict", "status", "sub", "proj", "form", "manual_input"]
# pre.set_session_keys(SESSION_KEYS)
tables = ["projects"]
with st.spinner("loading source data from DB ..."):
    pre.load_md_data_to_session_state(tables)
ss = st.session_state
conn: md.MotherDuck = ss.db_conn
projects_df: pl.DataFrame = ss.projects

with st.sidebar:
    st.toggle("toggle Dev Mode", key="dev")
if ss.dev:
    st.write(ss)


st.title("✅ Project Name Checker")
st.subheader("Check Xero Names Against the list of Projects in Trello")
"---"

projects_list = projects_df["name"].sort().to_list()
projects_list.insert(0, "")
selected_project_name = st.selectbox(
    "Type the job name to check what name will match the project name.",
    projects_list,
    key="selected_project_name",
)
