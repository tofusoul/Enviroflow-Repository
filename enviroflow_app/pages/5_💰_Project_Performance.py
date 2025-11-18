"""Project Performance Analysis Page.

This module provides a Streamlit interface for analyzing project performance metrics,
including profitability analysis, labour costs, and project timelines.
"""

import random
from typing import Any, cast

import polars as pl
import streamlit as st
from loguru import logger

from enviroflow_app import config
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.transform.from_projects_data import Projects_Data
from enviroflow_app.elt.transform.from_projects_dict import From_Project_Dicts
from enviroflow_app.model import Project
from enviroflow_app.st_components import pre, widgets

_ = logger.configure(**cast("dict[str, Any]", config.APP_LOG_CONF))


_ = pre.setup_streamlit_page()
pre.init_default_session()
pre.set_session_keys("projects_dict")
st.title("💰 Project Performance")

with st.spinner("loading source data from DB ..."):
    pre.load_md_data_to_session_state(
        tables=[
            "quotes",
            "projects",
            "labour_hours",
            "jobs_for_analytics",
            "xero_costs",
        ],
    )
ss = st.session_state
conn: md.MotherDuck = ss.db_conn
projects_df: pl.DataFrame = ss.projects
quotes_df: pl.DataFrame = ss.quotes
jobs_df: pl.DataFrame = ss.jobs_for_analytics
labour_hours_df = ss.labour_hours
costs_df = ss.xero_costs

with st.sidebar:
    _ = st.toggle("toggle Dev Mode", key="dev")


if ss.projects_dict is None:
    with st.spinner("Building Project Data"):
        projects_data: dict[str, Project] = Projects_Data(
            projects_df=projects_df,
            jobs_df=jobs_df,
            quotes_df=quotes_df,
            labour_hours_df=labour_hours_df,
            costs_df=costs_df,
        ).projects_dict
        ss.projects_dict = projects_data

projects_table = From_Project_Dicts(projects=ss.projects_dict).projects_table
st.write(projects_table.to_pandas())
auto_save_project_table = st.toggle("Auto Save Project Table", value=True)
if auto_save_project_table:
    widgets.st_save_table(
        conn=conn,
        table_name="projects_for_analytics",
        table=projects_table,
    )
else:
    save_table_to_db = st.button("Save Table to DB")
    if save_table_to_db:
        widgets.st_save_table(
            conn=conn,
            table_name="projects_for_analytics",
            table=projects_table,
        )


def check_project(project: Project) -> None:
    """Render the project details.

    Args:
        project: The project object to display details for.

    """
    st.write(f"## {project.name}")
    st.write(f"{project.statuses}")
    for i in project.job_cards_urls:
        st.write(f"{i}")
    if project.booking_date is not None:
        st.write(f"{project.booking_date.date()}")
    if project.longitude is not None:
        st.write(project.longitude, project.latitude)
    with st.expander("quotes"):
        if project.quotes is not None:
            for i in project.quotes:
                st.write(i.quote_lines.to_pandas())
    st.write(f"total_quote_value= ${project.total_quote_value}")
    if project.labour_table is not None:
        st.write(project.labour_table.to_pandas())
        st.write(f"labour cost=${project.labour_costs_total}")
        st.write(f"project_start {project.work_start}")
        st.write(f"project_end {project.work_end}")
    if project.supplier_costs is not None:
        st.write(project.supplier_costs.to_pandas())
        st.write(f"supplier costs = ${project.supplier_costs_total}")
    if project.gross_profit is not None:
        st.write(f"gross profit =${project.gross_profit}")
        st.write(f"gross profit margin = {project.gp_margin_pct * 100}%")
    st.write(f"est. project overhead = ${project.est_proj_overhead}")
    if project.gross_profit is not None:
        est_profit = round(project.gross_profit - project.est_proj_overhead, 2)
        st.write(f"est. profit = ${est_profit}")
    with st.expander("raw object"):
        st.write(project)


default = "1/40 Maryhill + 2/40 Maryhill"
projects: dict[str, Project] = ss.projects_dict
project_names = list(projects.keys())
project_names.insert(0, default)
selected_project_name = st.selectbox("select project", project_names)
if selected_project_name is not None:
    selected_project: Project = projects[selected_project_name]
    with st.container(border=True):
        check_project(selected_project)


samples = random.sample(list(projects.items()), 5)
sample_dict = {i[0]: i[1] for i in samples}
for v in sample_dict.values():
    with st.expander(v.name):
        st.write(v)
