# standard libaray imports
import asyncio
import os

# hack to import in the dir above the current dir
import sys
from pathlib import Path

import polars as pl
from loguru import logger

# thrid party libary imports
from streamlit import secrets

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

# custom modules import
from enviroflow_app import config
from enviroflow_app.elt.motherduck import md
from enviroflow_app.elt.trello import tr_api, tr_extract, tr_load
from enviroflow_app.elt.trello.tr_model import Board


def _get_motherduck_token():
    """Get MotherDuck token from environment variable or Streamlit secrets."""
    token = os.getenv("MOTHER_DUCK")
    if token:
        return token
    return secrets["motherduck"]["token"]


def _get_trello_credentials():
    """Get Trello credentials from environment variables or Streamlit secrets."""
    api_key = os.getenv("TRELLO_KEY")
    api_token = os.getenv("TRELLO_TOKEN")

    if api_key and api_token:
        return api_key, api_token

    return secrets["trello"]["api_key"], secrets["trello"]["api_token"]


CONN = md.MotherDuck(db_name="enviroflow", token=_get_motherduck_token())
api_key, api_token = _get_trello_credentials()
TR = tr_api.TrCreds(api_key=api_key, api_token=api_token)
RELEVANT_BOARDS: dict[str, str] = config.TR["relevant_trello_boards"]
# TEST_BOARDS = RELEVANT_BOARDS.copy()
# del TEST_BOARDS["Closed Jobs"]
# del TEST_BOARDS["Survey Workflow"]
#


async def save_board_keys_table_to_mother_duck(
    conn: md.MotherDuck,
    tr_conn: tr_api.TrCreds,
) -> pl.DataFrame | None:
    """Fetches the Trello Board Keys Table and Saves it to Motherduck"""
    logger.info("request sent getting trello board keys...")
    res = await tr_extract.get_board_key_df(tr_conn)
    if res is not None:
        board_keys_table: pl.DataFrame = res
        logger.info("saving trello board keys table to motherduck:")
        logger.info(res)
        conn.save_table("trello_board_keys", board_keys_table)
        return board_keys_table
    logger.error("something went wrong, no board keys data found")


async def save_job_cards_as_md_table(
    tr_conn: tr_api.TrCreds,
    relevant_boards: dict,
    dd_conn: md.MotherDuck,
) -> pl.DataFrame:
    logger.info("loading job cards from trello...")
    boards_dict: dict[str, Board] = await tr_extract.fetch_boards(
        tr_con=tr_conn,
        relevant_boards=relevant_boards,
    )
    # print_boards_info(boards=boards_dict)
    logger.info(f"boards loaded: {boards_dict.keys()}")
    job_cards: pl.DataFrame = tr_load.build_cards_df_from_boards_dict(
        boards_dict=boards_dict,
    )
    dd_conn.save_table(table_name="job_cards", table=job_cards)
    logger.info("saved job cards to motherduck")
    return job_cards


if __name__ == "__main__":
    asyncio.run(
        save_job_cards_as_md_table(
            dd_conn=CONN,
            tr_conn=TR,
            relevant_boards=RELEVANT_BOARDS,
        ),
    )
