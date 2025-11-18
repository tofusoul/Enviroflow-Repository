import polars as pl
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from enviroflow_app.elt.motherduck import md
from enviroflow_app.st_components.pre import init_default_session, setup_streamlit_page
from enviroflow_app.st_components.widgets import st_save_table

DUCK_TOKEN = st.secrets["motherduck"]["token"]
DB_NAME = "enviroflow"
SS = st.session_state
setup_streamlit_page()
init_default_session()
md_conn = md.MotherDuck(token=DUCK_TOKEN, db_name=DB_NAME)

# TODO set get the basic permission tables going


st.title("✏️ Edit_Data")
if SS["dev"]:
    st.write(SS)
    with st.expander("ctx"):
        ctx = get_script_run_ctx()
        if ctx:
            st.write(ctx)

with st.sidebar:
    st.checkbox("Dev Mode", key="dev")


def edit_table(conn: md.MotherDuck, table_name: str):
    source_table = conn.get_table(table_name=table_name)
    edited_table = st.data_editor(source_table.to_pandas(), num_rows="dynamic")
    save_edits = st.button("Save Edits")
    if save_edits:
        st_save_table(
            conn=conn,
            table_name=table_name,
            table=pl.from_pandas(edited_table),
        )


(
    quote_grouping,
    staff,
    subs,
) = st.tabs(["Quote Grouping", "Staff Data", "Subcontractor Data"])


with staff:
    edit_table(conn=md_conn, table_name="staff")

# tested example of implimenting a filter on the
# q_str = filter_table_by_column_value(
#     table_name="jobs",
#     column_name="address",
#     ilike_matches=["cheyenne"],
#     ilike_exceptions=["east"],
# )
#
# st.write(q_str)
# jobs = ddb.conn.sql(q_str).fetchdf()
# st.data_editor(jobs)
