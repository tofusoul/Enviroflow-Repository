import asyncio

import polars as pl
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from enviroflow_app.elt import tr2duck
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.trello import tr_api
from enviroflow_app.st_components.st_logger import Log_Level, st_logger


def load_trello_data_to_md(
    conn: md.MotherDuck,
    tr_conn: tr_api.TrCreds,
    relevant_boards: dict,
    render_target: DeltaGenerator,
) -> pl.DataFrame:
    """Renderes the ui for the trello data sync and retunrs the trello cards table"""
    with render_target:
        with st.spinner(" ⇵ syncing Trello board data to motherduck"):
            st_logger(Log_Level.INFO, "syncing trello_boards to mother duck")
            cards_table = asyncio.run(
                tr2duck.save_job_cards_as_md_table(
                    dd_conn=conn,
                    tr_conn=tr_conn,
                    relevant_boards=relevant_boards,
                ),
            )
    with st.sidebar:
        st.success(
            f"synced boards {[relevant_boards.keys()]!s} table to mother duck",
        )
        st_logger(Log_Level.SUCCESS, "synced trello to mother duck")

    render_target.caption("💾 The board data below has been saved on Motherduck")
    with render_target:
        st.data_editor(cards_table.to_pandas())
    return cards_table
