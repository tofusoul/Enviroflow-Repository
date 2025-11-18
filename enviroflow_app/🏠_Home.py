import streamlit as st
from loguru import logger

from enviroflow_app import config
from enviroflow_app.elt.transform.from_job_cards import From_Job_Cards
from enviroflow_app.elt.transform.from_quotes import From_Quotes_Data
from enviroflow_app.st_components import pre

logger.configure(**config.APP_LOG_CONF)
pre.setup_streamlit_page()
pre.init_default_session()
pre.load_md_data_to_session_state(tables=["quotes", "job_cards"])
ss = st.session_state
conn = ss.db_conn
quotes = ss.quotes
job_cards = ss.job_cards

with st.sidebar:
    st.toggle("toggle Dev Mode", key="dev")
if ss.dev:
    with st.popover("Check Session State"):
        st.write(ss)


# uncomment one of the below for the app to rerout to the
# page = "pages/1_📊_Overview_Reports.py"
# page = "pages/3_💸_Cost_Calcs.py"
# page = "pages/2_📦_Project_Planning.py"
# page = "pages/4_🪛_Subcontractors.py"
# page = "pages/5_💰_Project_Performance.py"
# page = "pages/6_🚚_Data_Loading_ELT.py"
page = "pages/7_🔮_Data_Explorer.py"
# page = "pages/8_✏️_Edit_Data.py"
# page = "pages/9_🖥️_Admin_Tools.py"
# page = "pages/3_📝_Subcontract_Generator.py"
# page = "pages/6_🚚_Data_Loading_ELT.py"

st.switch_page(page)


customers = From_Job_Cards(job_cards).customers_df
save_customer_table = st.button("save customers")
if save_customer_table:
    conn.save_table_to_md(table_name="customers", table=customers)
st.write(customers.to_pandas())

st.write(From_Quotes_Data(ss.quotes).jobs2quotes_map)
