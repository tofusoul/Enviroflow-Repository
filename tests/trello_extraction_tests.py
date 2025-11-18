import pytest
from streamlit import secrets
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# hack to import in the dir above the current dir
import polars as pl
import sys
from pathlib import Path

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from enviroflow_app import elt, config


@pytest.fixture
def relevant_boards():
    return config.TR["relevant_trello_boards"]


@pytest.fixture
def tr_con():
    return elt.trello.tr_api.TrCreds(
        api_key=secrets["trello"]["api_key"], api_token=secrets["trello"]["api_token"]
    )


@pytest.fixture
def con():
    return elt.motherduck.funcs.connect_ddb_via_ibis(
        location=elt.motherduck.funcs.DuckDB_Loc.MOTHERDUCK,
        db_name="enviroflow",
        token=secrets["motherduck"]["token"],
    )


@pytest.mark.asyncio
async def test_get_board_key_df(tr_con):
    res = await elt.trello.extract.get_tr_board_key_df(tr_con=tr_con)
    assert isinstance(res, pl.DataFrame)
    assert res.shape[1] == 3


@pytest.mark.asyncio
async def test_build_board_from_api_call(tr_con, relevant_boards):
    board_id = relevant_boards["Current Drainage Work"]
    board = await elt.trello.extract.get_board_as_object(
        board_id=board_id, tr_con=tr_con
    )
    assert isinstance(board, elt.trello.model.Board)
    assert isinstance(board.name, str)


@pytest.mark.asyncio
async def test_data_on_mother_duck_matches_trello_board_after_function_run(con, tr_con):
    """
    test that the data from the board object is apprpriately transpated into
    """
    pass
