import polars as pl
import streamlit as st
from loguru import logger

from enviroflow_app import config
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.transform.table_ops import update_items_budget_table
from enviroflow_app.model import Sales_Item, build_sales_items_from_tables
from enviroflow_app.st_components import pre
from enviroflow_app.st_components.cost_calc_components.show_sales_items import (
    cost_items_editor,
)
from enviroflow_app.st_components.widgets import st_save_table

table_names = [
    "items_budget",
    "cost_calcs",
    "quote_lookup_map",
    "users",
    "staff",
]
logger.configure(**config.APP_LOG_CONF)
pre.setup_streamlit_page("Cost Calculations")
pre.init_default_session()
pre.load_md_data_to_session_state(table_names)
ss = st.session_state
tables = {i: ss[i] for i in table_names}
sales_dict: dict[str, Sales_Item] = build_sales_items_from_tables(
    tables["items_budget"],
    tables["cost_calcs"],
)
name_lookup = {i["email"]: i["name"] for i in ss.users.to_dicts()}
conn = ss.db_conn
user_email = st.user.email
user_name = name_lookup[user_email]


def line_cost_builder(
    items_budget: pl.DataFrame,
    sales_dict: dict[str, Sales_Item],
    md_conn: md.MotherDuck,
) -> None:
    pre.add_object_to_session_state("sales_items", sales_dict)
    items_budget_table = st.data_editor(
        items_budget.to_pandas(),
        num_rows="dynamic",
        use_container_width=True,
    )
    save_edits = st.button("Save Direct Edits")

    if save_edits:
        ss.items_budget = pl.from_pandas(items_budget_table)
        st_save_table(
            conn=md_conn,
            table_name="items_budget",
            table=pl.from_pandas(items_budget_table),
        )
    saved = cost_items_editor(ss.sales_items)
    st.write(saved)
    regen_items_budget = st.button("Regenerate Items Budget Table")
    if regen_items_budget:
        update_items_budget_table(md_conn)


def labour_rates_builder():
    st.data_editor(ss.staff.to_pandas())


def overhead_builder():
    pass


def page(
    tables: dict[str, pl.DataFrame],
    conn: md.MotherDuck,
    sales_dict: dict[str, Sales_Item],
):
    st.info(
        f"logged in as {user_name}. Yourealing with senstive business info, please exercise caution",
    )
    line_costs, labour_rates, overhead = st.tabs(
        ["Line Cost Buildup", "Labour Rate", "Project Overhead"],
    )
    with line_costs:
        line_cost_builder(
            items_budget=tables["items_budget"],
            sales_dict=sales_dict,
            md_conn=conn,
        )
    with labour_rates:
        labour_rates_builder()
    with overhead:
        overhead_builder()
    pre.debug_toggle()


ALLOWED_IN_PAGE = ["test@example.com", "ryan@enviroflo.co.nz", "andrew@enviroflo.co.nz"]

if __name__ == "__main__":
    if user_email in ALLOWED_IN_PAGE:
        page(tables=tables, conn=ss.db_conn, sales_dict=sales_dict)
    else:
        st.error(
            f"{user_name},you are not allowed here, check with Ryan and Hayden if you need this information",
        )
