import random
from typing import Tuple

import polars as pl
import streamlit as st
from duckdb import ConnectionException

from enviroflow_app.elt.motherduck import md
from enviroflow_app.model import Job, Project

from .st_logger import Log_Level, st_logger


def st_save_table(conn: md.MotherDuck, table_name: str, table: pl.DataFrame) -> None:
    """Saves a pl dataframe to the db,"""
    st_logger(
        Log_Level.INFO,
        f"💾 saving {table_name} table to the db (shape: {table.shape})",
    )
    try:
        conn.save_table(table_name=table_name, table=table)
    except ConnectionException as e:
        st_logger(Log_Level.ERROR, f"🚨 propblem connecting to DB {e}, ")
    st_logger(Log_Level.INFO, f" 👌saved {table_name} table to the db")


def display_and_update_debug_tables(
    conn: md.MotherDuck,
    tables: Tuple[str, pl.DataFrame] | list[Tuple[str, pl.DataFrame]],
):
    def save_display_and_update_table(table_name: str, table: pl.DataFrame) -> None:
        st_save_table(conn=conn, table_name=table_name, table=table)
        st.write(f"**{table_name}**")
        st.dataframe(table.to_pandas())

    with st.expander("🐞 debug tables"):
        if isinstance(tables, list):
            for table in tables:
                save_display_and_update_table(table_name=table[0], table=table[1])
        else:
            save_display_and_update_table(table_name=tables[0], table=tables[1])


def add_additional_item() -> Tuple[str, int] | None:
    additional_item = st.text_area(
        label="Additional Items",
        placeholder="Enter additional items here, separated by commas",
    )
    additiona_item_qty = st.number_input(
        label="Additional Items Quantity",
        value=1,
        step=1,
    )
    return (additional_item, additiona_item_qty)


def view_jobs(jobs: dict[str, Job] | Job, sample: int | None = 5) -> None:
    def view_job(job: Job) -> None:
        with st.expander(name):
            st.write(job.status)
            st.write(job.id)
            st.write(job.url)
            st.write(f"{job.shared_drains=}")
            # st.write("_customer details_")
            # st.write(job.customer_details)
            st.write("_qty_from_card_")
            st.write(job.qty_from_card)
            st.write("_labels_")
            st.write(job.labels)
            st.write("_drive_folder_link_")
            st.write(job.drive_folder_link)
            st.write("_linked_cards_")
            st.write(job.linked_cards)
            st.write("_sorted_attatchments_")
            st.write(job.sorted_attatchments)
            st.write("_timeline_")
            st.write(job.timeline)
            st.write("_quotes_")
            st.write(job.quotes)
            st.write("_variation_quotes_")
            st.write(job.variation_quotes)
            st.write("_shared_with_")
            st.write(job.shared_with)
            st.write(job.site_staff)
            st.write(job.labour_records)
            st.write(job.labour_records)
            st.write(job.parse_notes)

    if isinstance(jobs, Job):
        view_job(jobs)
    else:
        if sample is not None:
            sample_jobs = random.sample(list(jobs.values()), sample)
            jobs = {job.name: job for job in sample_jobs}
        for name, job in jobs.items():
            view_job(job)


def render_project_links(project: Project):
    """Renders links given project"""
    for job in project.jobs if project.jobs is not None else []:
        if job is None:
            continue
        try:
            st.markdown(
                f"**{job.name}**: [{job.status}] [[🔗Trello Card]({job.url})] [[📂Drive Link]({job.drive_folder_link[0]})]",
            )
        except AttributeError:
            st.write(f"Job object encountered AttributeError: {job!r}")
            st_logger(
                level=Log_Level.ERROR,
                message=f"project {job} not a valid job it is : {type(project)}",
            )
        except IndexError:
            st.write(
                f"**{job.name}**: [{job.status}] [[🔗Trello Card]({job.url})] ~[📂*No Drive Link*]~)",
            )
            st_logger(level=Log_Level.ERROR, message="no link in job's drive folder")
