import asyncio
from pathlib import Path
from typing import Tuple

import polars as pl
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from enviroflow_app.elt import float2duck, tr2duck
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.transform.from_job_cards import (
    From_Job_Cards,
    Job_Parse_Results,
)
from enviroflow_app.elt.transform.from_jobs import From_Jobs_Df, From_Jobs_Dict
from enviroflow_app.elt.transform.from_jobs_with_labour import From_Jobs_With_Labour
from enviroflow_app.elt.transform.from_labour_records import (
    From_Labour_Records,
    Jobs_With_Labour_Results,
)
from enviroflow_app.elt.transform.from_projects_dict import From_Raw_Projects_Dict
from enviroflow_app.elt.transform.from_quotes import From_Quotes_Data
from enviroflow_app.elt.transform.table_ops import stitch_quotes_on_md
from enviroflow_app.elt.trello import tr_api
from enviroflow_app.elt.trello.tr_api_async import get_actions_with_card_id
from enviroflow_app.model import Job, Quote
from enviroflow_app.st_components.pre import save_table_to_ss
from enviroflow_app.st_components.widgets import (
    display_and_update_debug_tables,
    st_save_table,
    view_jobs,
)

from .st_logger import Log_Level, st_logger

ss = st.session_state


def sync_trello(
    conn: md.MotherDuck,
    tr_conn: tr_api.TrCreds,
    relevant_boards: dict,
    render_target: DeltaGenerator,
) -> pl.DataFrame:
    """Renderes the ui for the trello data sync and retunrs the trello cards table"""
    with render_target:
        with st.spinner(" ⇵ syncing Trello board data to motherduck"):
            st_logger(Log_Level.INFO, "syncing trello_boards to mother duck")
            asyncio.run(
                tr2duck.save_board_keys_table_to_mother_duck(
                    conn=conn, tr_conn=tr_conn
                ),
            )
            cards_table = asyncio.run(
                tr2duck.save_job_cards_as_md_table(
                    dd_conn=conn,
                    tr_conn=tr_conn,
                    relevant_boards=relevant_boards,
                ),
            )
            st.data_editor(cards_table.to_pandas())
    with st.sidebar:
        st.success(
            f"synced boards {[relevant_boards.keys()]!s} table to mother duck",
        )
        st_logger(Log_Level.SUCCESS, "synced trello to mother duck")
    return cards_table

    render_target.caption("💾 The board data below has been saved on Motherduck")
    with render_target:
        st.data_editor(cards_table.to_pandas())
    return cards_table


def legacy_file_sync(
    conn: md.MotherDuck,
    file_paths_dict: dict[str, Path],
    render_target: DeltaGenerator,
) -> None:
    sync_list = {}
    for name, path in file_paths_dict.items():
        if path.suffix == ".parquet":
            sync_list[name] = pl.read_parquet(path)
        elif path.suffix == ".csv":
            sync_list[name] = pl.read_csv(path, infer_schema_length=10_000)
        else:
            raise ValueError(f"unsupported file type {path.suffix}")
    st.sidebar.caption("💾 saving the legacy tables to motherduck.")
    for name, table in sync_list.items():
        st_logger(
            Log_Level.INFO,
            f"💾 saving {name} table to the db (shape: {table.shape})",
        )
        table: pl.DataFrame  # type annotation for editor tooling
        conn.save_table(table_name=name, table=table)
        st_logger(
            Log_Level.INFO,
            f"👌 saved {name} table to the db (shape: {table.shape})",
        )
        table_dtypes = {k: v for k, v in zip(table.columns, table.dtypes)}
        with st.sidebar:
            st.success(f"👌 saved {name} table")
        render_target.caption("data details below")
        with render_target:
            with st.expander(f"show {name} table details"):
                st.caption("table_dtypes")
                st.write(table_dtypes)
                st.dataframe(table)


def sync_float(
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
    ss["labour_hours"] = float_data
    st_logger(Log_Level.SUCCESS, "saved float data to session state")
    with render_target:
        st.data_editor(float_data.to_pandas())
    return float_data


def stitch_db_quotes(
    conn: md.MotherDuck,
    render_target: DeltaGenerator,
) -> pl.DataFrame:
    st_logger(Log_Level.INFO, "🪄 updating quotes table with quote data")
    with render_target:
        with st.spinner("updating quotes..."):
            quotes = stitch_quotes_on_md(conn)
    st.sidebar.success("quotes updated on db")
    render_target.write(quotes.to_pandas())
    return quotes


def gen_customers_table(
    conn: md.MotherDuck,
    job_cards: pl.DataFrame,
    render_target: DeltaGenerator,
) -> pl.DataFrame:
    with render_target:
        with st.spinner("generating and saving customers table..."):
            st_logger(Log_Level.INFO, "🪄 generating customers table")
            customer_table = From_Job_Cards(job_cards).customers_df
            conn.save_table(table_name="customers", table=customer_table)
    st.sidebar.success("customers table generated")
    render_target.write(customer_table.to_pandas())
    return customer_table


def build_save_jobs(
    conn: md.MotherDuck,
    job_cards: pl.DataFrame,
    quotes: pl.DataFrame,
    render_target: DeltaGenerator,
) -> Tuple[Job_Parse_Results, pl.DataFrame]:
    st_logger(Log_Level.INFO, "🪄 building jobs table")
    results: Job_Parse_Results = From_Job_Cards(job_cards).build_jobs_dict(
        jobs2quotes_map=From_Quotes_Data(quotes).jobs2quotes_map,
    )
    jobs = From_Jobs_Dict(results.jobs).jobs_df
    no_quotes_matched = From_Jobs_Dict(results.no_quotes_matched).jobs_df
    job_attatched_cards_not_parsed: pl.DataFrame = pl.from_dicts(
        results.attatched_card_not_parsed,
    )
    st_save_table(conn=conn, table_name="jobs", table=jobs)
    st.sidebar.success("👌 saved jobs table")
    render_target.write("### Jobs Table")
    render_target.dataframe(jobs.to_pandas())
    render_target.info(" 💾 🐞 saving debug tables")
    with render_target:
        display_and_update_debug_tables(
            conn=conn,
            tables=[
                ("removed_cards", results.removed_cards),
                ("job_no_quotes_matched", no_quotes_matched),
                ("job_attached_cards_not_jobs", job_attatched_cards_not_parsed),
            ],
        )
    msg = "👌 saved jobs table related debug tables"
    st_logger(Log_Level.SUCCESS, msg)
    st.sidebar.success(msg)
    return results, jobs


def add_labour_hours_to_jobs(
    conn: md.MotherDuck,
    labour_hours: pl.DataFrame,
    quotes_dict: dict[str, Quote],
    render_target: DeltaGenerator,
) -> Tuple[Jobs_With_Labour_Results, pl.DataFrame]:
    if "jobs" not in ss or ss["jobs"] is None:
        st_logger(Log_Level.INFO, "📖 fetching jobs table from DB")
        jobs = conn.get_table("jobs")
    elif type(ss["jobs"]) is pl.DataFrame:
        st_logger(Log_Level.INFO, "📖 loading jobs table from session")
        jobs = ss["jobs"]
    else:
        raise ValueError(f"Unexpcted type for jobs: {type(ss['jobs'])}")

    msg = "🏗️ Built jobs with labour hours table"
    st_logger(Log_Level.SUCCESS, msg)
    st.sidebar.success(msg)

    results = From_Labour_Records(labour_hours).jobs_with_labour(jobs)

    render_target.write("### Jobs With Labour Hours")
    st_save_table(conn=conn, table_name="jobs_with_hours", table=results.jobs_df)
    render_target.dataframe(results.jobs_df.to_pandas())
    render_target.write("### job_analytics_table")
    jobs_for_analytics = From_Jobs_With_Labour(
        results.jobs_df,
        quotes_dict,
    ).job_analytics_table
    st_save_table(conn=conn, table_name="jobs_for_analytics", table=jobs_for_analytics)
    st.write(jobs_for_analytics.to_pandas())
    return results, jobs_for_analytics

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


def parse_db_jobs(
    conn: md.MotherDuck,
    quotes: pl.DataFrame,
    render_target: DeltaGenerator,
) -> dict[str, Job]:
    st_logger(Log_Level.INFO, "🪄 parsing jobs from db")
    jobs_df = conn.get_table("jobs")
    jobs = From_Jobs_Df(jobs_df).jobs_dict(quotes=From_Quotes_Data(quotes).quotes_dict)
    with render_target:
        view_jobs(jobs, sample=5)
    return jobs


def build_projects(
    conn: md.MotherDuck,
    jobs_with_labour_hours: pl.DataFrame,
    quotes_dict: dict[str, Quote],
    render_target: DeltaGenerator,
) -> pl.DataFrame:
    st_logger(Log_Level.INFO, "🪄 building projects")
    with render_target:
        with st.spinner("building projects"):
            st_logger(Log_Level.INFO, "🪄 building_shared_drains grups ")
            projects = From_Jobs_With_Labour(
                jobs_with_labour_hours,
                quotes_dict,
            ).projects
            st_logger(level=Log_Level.INFO, message="🪄 building projects table")
            with st.spinner("building projects table"):
                projects_df = From_Raw_Projects_Dict(projects).projects_table
                st.write(projects_df)
            with st.spinner("saving table to motherduck"):
                st_save_table(conn=conn, table_name="projects", table=projects_df)
    return projects_df


def sync_all_data(
    file_paths_dict: dict[str, Path],
    conn: md.MotherDuck,
    relevant_boards: dict,
    tr_conn: tr_api.TrCreds,
    render_target: DeltaGenerator,
) -> None:
    st_logger(Log_Level.INFO, "🔁 updating all data")
    legacy_file_sync(
        conn=conn,
        file_paths_dict=file_paths_dict,
        render_target=render_target,
    )
    trello_cards = sync_trello(
        conn=conn,
        tr_conn=tr_conn,
        relevant_boards=relevant_boards,
        render_target=render_target,
    )
    ss["job_cards"] = trello_cards
    st_logger(Log_Level.SUCCESS, "synced trello cards to session state")

    float_data = sync_float(
        conn=conn,
        render_target=render_target,
    )
    ss["labour_hours"] = float_data
    st_logger(Log_Level.SUCCESS, "synced float data to session state")

    quotes = stitch_db_quotes(
        conn=conn,
        render_target=render_target,
    )
    ss["quotes"] = quotes
    st_logger(Log_Level.SUCCESS, "synced quotes to session state")

    customers = gen_customers_table(
        conn=conn,
        job_cards=ss["job_cards"],
        render_target=render_target,
    )
    save_table_to_ss("customers", customers)

    jobs = build_save_jobs(
        conn=conn,
        job_cards=ss["job_cards"],
        quotes=ss["quotes"],
        render_target=render_target,
    )
    ss["jobs"] = jobs[1]
    st_logger(Log_Level.SUCCESS, "synced job to session state")

    parse_db_jobs(
        conn=conn,
        quotes=ss["quotes"],
        render_target=render_target,
    )

    jobs_with_hours_results = add_labour_hours_to_jobs(
        conn=conn,
        quotes_dict=From_Quotes_Data(quotes).quotes_dict,
        labour_hours=ss["labour_hours"],
        render_target=render_target,
    )
    ss["jobs_with_hours"] = jobs_with_hours_results[1]
    st_logger(Log_Level.SUCCESS, "synced jobs with hours to session state")

    projects_df = build_projects(
        conn=conn,
        quotes_dict=From_Quotes_Data(quotes).quotes_dict,
        jobs_with_labour_hours=ss["jobs_with_hours"],
        render_target=render_target,
    )
    ss["projects"] = projects_df
    st_logger(Log_Level.SUCCESS, "synced projects to session state")


def page(
    file_paths_dict: dict[str, Path],
    conn: md.MotherDuck,
    relevant_boards: dict,
    tr_conn: tr_api.TrCreds,
) -> None:
    ctrls, main_panel = st.columns([1, 2])
    ctrls.caption("👇 buttons to press")
    with ctrls.container(border=True):
        sync_files = st.button("Sync Files from Legacy Data Flow")
        stitch_quotes = st.button("Update Quotes Table")
        trello_sync = st.button("Sync Boards Data")
        build_jobs = st.button("Build Jobs and Save to DB")
        float_sync = st.button("Sync Float Data")
        gen_cust = st.button("Regnerate Customers Table")
        hours_to_jobs = st.button("Load Labour Hours to Jobs")
        load_db_jobs = st.button("Parse Jobs from DB")
        build_projects_df = st.button("Build Project Table")
        test = st.button("Test")
    update_all_data = ctrls.button("Update All Data")
    main_panel.caption("📺 results shown 👇 here")
    main_panel_content = main_panel.container(border=True)
    main_panel_content.caption(
        "🖥️ widgets and data when you press the button will be shown 👇 here",
    )

    if sync_files:
        legacy_file_sync(
            conn=conn,
            file_paths_dict=file_paths_dict,
            render_target=main_panel_content,
        )
    if trello_sync:
        trello_cards = sync_trello(
            conn=conn,
            tr_conn=tr_conn,
            relevant_boards=relevant_boards,
            render_target=main_panel_content,
        )
        ss["job_cards"] = trello_cards
        st_logger(Log_Level.SUCCESS, "synced trello cards to session state")

    if float_sync:
        float_data = sync_float(
            conn=conn,
            render_target=main_panel_content,
        )
        ss["labour_hours"] = float_data
        st_logger(Log_Level.SUCCESS, "synced float data to session state")

    if stitch_quotes:
        quotes = stitch_db_quotes(
            conn=conn,
            render_target=main_panel_content,
        )
        ss["quotes"] = quotes
        st_logger(Log_Level.SUCCESS, "synced quotes to session state")

    if gen_cust:
        customers = gen_customers_table(
            conn=conn,
            job_cards=ss["job_cards"],
            render_target=main_panel_content,
        )
        save_table_to_ss("customers", customers)

    if build_jobs:
        jobs = build_save_jobs(
            conn=conn,
            job_cards=ss["job_cards"],
            quotes=ss["quotes"],
            render_target=main_panel_content,
        )
        ss["jobs"] = jobs[1]
        st_logger(Log_Level.SUCCESS, "synced job to session state")

    if load_db_jobs:
        parse_db_jobs(
            conn=conn,
            quotes=ss["quotes"],
            render_target=main_panel_content,
        )

    if hours_to_jobs:
        jobs_with_hours_results = add_labour_hours_to_jobs(
            conn=conn,
            quotes_dict=From_Quotes_Data(ss["quotes"]).quotes_dict,
            labour_hours=ss["labour_hours"],
            render_target=main_panel_content,
        )
        ss["jobs_with_hours"] = jobs_with_hours_results[1]
        st_logger(Log_Level.SUCCESS, "synced jobs with hours to session state")

    if update_all_data:
        sync_all_data(
            file_paths_dict=file_paths_dict,
            conn=conn,
            relevant_boards=relevant_boards,
            tr_conn=tr_conn,
            render_target=main_panel_content,
        )
    if build_projects_df:
        projects_df = build_projects(
            conn=conn,
            quotes_dict=From_Quotes_Data(ss["quotes"]).quotes_dict,
            jobs_with_labour_hours=ss["jobs_with_hours"],
            render_target=main_panel_content,
        )
        ss["projects"] = projects_df
        st_logger(Log_Level.SUCCESS, "synced projects to session state")

    if test:
        response = asyncio.run(
            get_actions_with_card_id(card_id="Q65Q9Jvv", tr_conn=tr_conn),
        )
        st.write(response.json())

    if st.session_state["dev"]:
        with st.expander("Check Session State"):
            st.write(st.session_state)
