""" """

import asyncio

import httpx
import orjson
import polars as pl
from loguru import logger

from enviroflow_app import config
from enviroflow_app.elt.motherduck import md

# Custom Modules
from enviroflow_app.elt.trello import tr_api
from enviroflow_app.elt.trello import tr_model as model

logger.configure(**config.TR_LOG_CONF)


async def get_board_key_df(
    tr_con: tr_api.TrCreds,
) -> pl.DataFrame:
    """Async version of the get board_keys df Function"""
    logger.info("getting trello boards...")
    res = await tr_api.get_boards_from_org(tr_conn=tr_con)
    if isinstance(res, httpx.Response):
        raw_org_data = res.json()
        logger.info("building trello_board_id_table")

        boards = {
            "name": [],
            "id": [],
            "url": [],
        }

        for board in raw_org_data:
            boards["name"].append(board["name"])
            boards["id"].append(board["id"])
            boards["url"].append(board["url"])

        data = {
            "board_names": boards["name"],
            "board_ids": boards["id"],
            "board_urls": boards["url"],
        }

        df = pl.DataFrame(data)
        return df
    raise ValueError("could not retreive boardkeys for keys table")


async def fetch_list_lookup(tr_con: tr_api.TrCreds, board_id: str) -> dict:
    """From the board id, fetches data and builds a dictionary with key as a trello list id, and value as list name"""
    list_res = await tr_api.get_lists_with_board_id(tr_conn=tr_con, board_id=board_id)
    raw_list_name_dict = orjson.loads(list_res.text)
    list_lookup = {i["id"]: i["name"] for i in raw_list_name_dict}
    return list_lookup


async def get_list_names_table(
    tr_con: tr_api.TrCreds,
    con: md.MotherDuck,
    board_id: str | None = None,
    board_id_dict: dict | None = None,
    board_keys_table: pl.DataFrame | None = None,
) -> pl.DataFrame | None:
    """Gets list names from trello of the supplied board id(s), and stiches together a human friendly lookup table, that replaces the board_id with board name and drops the irrelevant fields."""

    def build_list_table(res: httpx.Response) -> pl.DataFrame:
        df = (
            pl.from_dicts(orjson.loads(res.text))
            .filter(pl.col("closed") == "false")
            .drop(["pos", "subscribed", "softLimit", "status", "closed"])
        )
        return df

    # looks up the board keys table on ddb if it isn't supplied
    if board_keys_table is None:
        board_keys_table = con.get_table("trello_board_keys")
    else:
        pass

    # if board_id and bord_id_dict can't both be none, if they are, there's nothing todo
    if board_id is None and board_id_dict is None:
        logger.error("no board ids provided for api query")
        return None

    # if a board_id_dict is supplie , even if the caller supplies a board_id, it will be ignored
    if board_id_dict is not None:
        res_list = []
        for key, val in board_id_dict.items():
            logger.info(f"getting lists on board: {key}")
            res = asyncio.create_task(
                tr_api.get_lists_with_board_id(board_id=val, tr_conn=tr_con),
            )
        res_list = await asyncio.gather(*res_list)
        df_list = [build_list_table(i) for i in res_list]
        list_df = df_list[0]
        for i in df_list[1:]:
            list_df = pl.concat([list_df, i], rechunk=True)
        df = list_df.join(
            board_keys_table,
            left_on="idBoard",
            right_on="board_ids",
        ).drop(["idBoard", "board_urls"])
        return df

    # deal with board_id requests.
    if board_id is not None and board_id_dict is None:
        res = await tr_api.get_lists_with_board_id(board_id=board_id, tr_conn=tr_con)
        if type(res) is httpx.Response:
            return build_list_table(res)
        logger.error(f"type(res) = {type(res)} is not not an HTTPX Response.")

    # if none of the above scenarios apply nothing gets returned.
    else:
        return None


async def get_custom_fields_on_board(tr_con: tr_api.TrCreds) -> pl.DataFrame | None:
    board_id = config.TR["relevant_trello_boards"]["Current Drainage Work"]
    res = await tr_api.get_custom_fields_with_board_id(
        board_id=board_id,
        tr_conn=tr_con,
    )

    if isinstance(res, httpx.Response):
        body = res.json()
        df = pl.from_dicts(body)
        return df
    logger.error("could not get custom on board")


async def fetch_board_as_object(
    board_id: str,
    tr_con: tr_api.TrCreds,
) -> model.Board | httpx.Response | None:
    """Builds a Trello board object from the board id. This requires a couple of api call to the server:
    1. get a full json of the board
    2. get get the list name lookup
    """
    query_params = {
        "cards": "visible",
        # "checklists": "all",
        "card_fields": "all",
        "customFields": True,
        "card_customFieldItems": True,
        "card_labels": True,
        "card_idList": True,
        "attachments": True,
        "card_attachments": True,
        "attachment_fields": "all",
    }
    logger.info(f"querying trello board with id {board_id}")
    res = await tr_api.get_board_with_id(
        board_id=board_id,
        tr_conn=tr_con,
        params=query_params,
    )

    if res is not None:
        logger.info(
            f"recieved request for board with id: {board_id} with {res.status_code}",
        )
        list_lookup = await fetch_list_lookup(tr_con=tr_con, board_id=board_id)
        logger.info(f"parsing board with id {board_id}")
        # logger.info(res.json())
        board = model.Board(**res.json())
        board.set_list_names(list_lookup)  # type: ignore
        return board

    logger.error(f"could not get board with id {board_id}")
    return None


async def fetch_boards(
    tr_con: tr_api.TrCreds,
    relevant_boards: dict,
) -> dict[str, model.Board]:
    """With trello credientials (tr_con) and a relevant Boards dictionary, where the key is the board name and value the board id.  creates a dictioary with the board name as key and and the board object as value"""
    req_list = []
    for key, value in relevant_boards.items():
        logger.info(f"getting board {key} with id {value}")
        fetch_board = asyncio.create_task(
            fetch_board_as_object(board_id=value, tr_con=tr_con),
        )
        req_list.append(fetch_board)

    results = await asyncio.gather(*req_list)
    boards: list[model.Board] = results
    logger.info(f"Retrieved {len(boards)} board objects")
    boards_dict: dict[str, model.Board] = {b.name: b for b in boards}
    logger.info(f"boards objects created for the these bards: {boards_dict.keys()}")
    return boards_dict
