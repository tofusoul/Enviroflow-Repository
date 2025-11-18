import asyncio

import polars as pl
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from enviroflow_app.elt import float2duck
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.transform.from_labour_records import (
    From_Labour_Records,
    Jobs_With_Labour_Results,
)
from enviroflow_app.st_components.st_logger import Log_Level, st_logger
from enviroflow_app.st_components.widgets import (
    display_and_update_debug_tables,
    st_save_table,
)

ss = st.session_state


def build_labour_hours_from_float_data(
    conn: md.MotherDuck,
    render_target: DeltaGenerator,
) -> pl.DataFrame:
    with render_target:
        with st.spinner("syncing direct labour info to mother duck"):
            st_logger(Log_Level.INFO, "syncing labour to mother duck")
            float_data = asyncio.run(float2duck.build_project_labour_hours_table())

            # Remove duplicate rows before saving to MotherDuck
            original_count = len(float_data)
            float_data = float_data.unique()
            deduplicated_count = len(float_data)

            if original_count > deduplicated_count:
                duplicates_removed = original_count - deduplicated_count
                st_logger(
                    Log_Level.INFO,
                    f"removed {duplicates_removed} duplicate labour records",
                )
                st.sidebar.info(f"🧹 Removed {duplicates_removed} duplicate records")

            conn.save_table(table_name="labour_hours", table=float_data)
            with st.sidebar:
                st.success("synced float data info to mother duck")
                st_logger(Log_Level.SUCCESS, "synced float mother duck")
    render_target.write("💾 saved labour hours table")
    with render_target:
        st.data_editor(float_data.to_pandas())
    return float_data


def add_labour_hours_to_jobs(
    conn: md.MotherDuck,
    labour_hours: pl.DataFrame,
    render_target: DeltaGenerator,
) -> Jobs_With_Labour_Results:
    jobs = conn.get_table("jobs")

    msg = "🏗️ Built jobs with labour hours table"
    st_logger(Log_Level.SUCCESS, msg)
    st.sidebar.success(msg)

    results = From_Labour_Records(labour_hours).jobs_with_labour(jobs)

    render_target.write("### Jobs With Labour Hours")
    st_save_table(conn=conn, table_name="jobs_with_hours", table=results.jobs_df)
    render_target.dataframe(results.jobs_df.to_pandas())
    with render_target:
        display_and_update_debug_tables(
            conn=conn,
            tables=[
                ("aggregated_labour_hours", results.aggregated_df),
                ("removed_hours_records", results.removed),
                ("job_no_hours_records", results.job_no_hour_data),
            ],
        )
    return results
