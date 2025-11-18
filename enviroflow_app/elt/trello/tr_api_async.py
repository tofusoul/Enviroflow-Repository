import asyncio  # Add missing import for asyncio

# hack to import in the dir above the current dir
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import httpx
from loguru import logger

from enviroflow_app import config

logger.configure(**config.TR_LOG_CONF)

try:
    ORG_ID = config.TR["org_id"]
except KeyError:
    logger.error("No Trello organization id found")
    ORG_ID = ""
try:
    ORG_NAME = config.TR["org_name"]
except KeyError:
    logger.error("No Trello organization id found")
    ORG_NAME = ""

logger.configure(**config.TR_LOG_CONF)

BASE_URL = "https://trello.com/1"
HEADERS = config.TR["headers"]

ORG_URL = f"{BASE_URL}/organizations/{ORG_ID}"


class Board_Ops(Enum):
    DEL_BOARD = "/boards/{id}"
    DEL_REMOVE_MEMBER = "/boards/{id}/members/{idMember}"  # Implimented
    GET_ACTIONS_ON_BOARD = "/boards/{boardId}/actions"
    GET_BOARD = "/boards/{id}"
    GET_BOARD_MEMBERSHIPS = "/boards/{id}/memberships"
    GET_BOARD_STARS = "/boards/{boardId}/boardStars"
    GET_CARDS_ON_BOARD = "/boards/{id}/cards"
    GET_CARD_ON_BOARD = "/boards/{id}/cards/{idCard}"
    GET_CHECKLISTS_ON_BOARD = "/boards/{id}/checklists"
    GET_ENABLED_POWERUPS_ON_BOARD = "/boards/{id}/boardPlugins"
    GET_FIELD_ON_BOARD = "/boards/{id}/{field}"
    GET_FILTERED_CARDS_ON_BOARD = "/boards/{id}/cards/{filter}"
    GET_FILTERED_LISTS_ON_BOARD = "/boards/{id}/lists/{filter}"
    GET_GET_CUSTOM_FIELDS_ON_BOARD = "/boards/{id}/customFields"
    GET_LABELS_ON_BOARD = "/boards/{id}/labels"
    GET_LISTS_ON_BOARD = "/boards/{id}/lists"
    GET_MEMBERS_ON_BOARD = "/boards/{id}/members"
    GET_POWERUPS_ON_BOARD = "/boards/{id}/plugins"
    POST_CREATE_BOARD = "/boards/"
    POST_CREATE_CALENDAR_KEY = "/boards/{id}/calendarKey/generate"
    POST_CREATE_EMAIL_KEY = "/boards/{id}/emailKey/generate"
    POST_CREATE_LABEL = "/boards/{id}/labels"
    POST_CREATE_LIST = "/boards/{id}/lists"
    POST_CREATE_TAG = "/boards/{id}/idTags"
    POST_MARK_AS_VIEWED = "/boards/{id}/markedAsViewed"
    PUT_ADD_MEMBER = "/boards/{id}/members/{idMember}"
    PUT_BOARD = "/boards/{id}"
    PUT_INVITE_MEMBER_BY_EMAIL = "/boards/{id}/members"
    PUT_SET_DEFAULT_EMAIL_TO_BOARD_LIST = "/boards/{id}/myPrefs/idEmailList"
    PUT_SET_EMAIL_POSITION = "/boards/{id}/myPrefs/emailPosition"
    PUT_SET_SHOW_ACTIVITY_ON_SIDEBAR = "/boards/{id}/myPrefs/showSidebarActivity"
    PUT_SET_SHOW_BOARD_ACTIONS_ON_SIDEBAR = (
        "/boards/{id}/myPrefs/showSidebarBoardActions"
    )
    PUT_SET_SHOW_LIST_GUIDE = "/boards/{id}/myPrefs/showListGuide"
    PUT_SET_SHOW_MEMBERS_ON_SIDEBAR = "/boards/{id}/myPrefs/showSidebarMembers"
    PUT_SET_SHOW_SIDEBAR = "/boards/{id}/myPrefs/showSidebar"
    PUT_UPDATE_MEMBER_MEMBERSHIP = "/boards/{id}/memberships/{idMembership}"


class Card_Ops(Enum):
    DEL = "/cards/{id}"
    DEL_ATTATCHMENT = "/cards/{id}/attachments/{idAttachment}"
    DEL_CHECKLIST_ITEM = "/cards/{id}/checkItem/{idCheckItem}"
    DEL_CHECK_LIST = "/cards/{id}/checklists/{idChecklist}"
    DEL_COMMENT = "/cards/{id}/actions/{idAction}/comments"
    DEL_LABEL = "/cards/{id}/idLabels/{idLabel}"
    DEL_MEMBER = "/cards/{id}/idMembers/{idMember}"
    DEL_MEMBER_VOTES = "/cards/{id}/membersVoted/{idMember}"
    DEL_STICKER = "/cards/{id}/stickers/{idSticker}"
    GET = "/cards/{id}"
    GET_ATIONS = "/cards/{id}/actions"
    GET_ATTATCHMENT = "/cards/{id}/attachments/{idAttachment}"
    GET_A_FIELD = "/cards/{id}/{field}"
    GET_BOARD = "/cards/{id}/board"
    GET_CHECKLISTS = "/cards/{id}/checklists"
    GET_CHECKLIST_ITEM = "/cards/{id}/checkItem/{idCheckItem}"
    GET_COMPLETED_CHECKLIST_ITEMS = "/cards/{id}/checkItemStates"
    GET_CUSTOM_FIELD_ITEMS = "/cards/{id}/customFieldItems"
    GET_LIST = "/cards/{id}/list"
    GET_MEMBERS = "/cards/{id}/members"
    GET_MEMBER_VOTES = "/cards/{id}/membersVoted"
    GET_PLUGIN_DATA = "/cards/{id}/pluginData"
    GET_STICKER = "/cards/{id}/stickers/{idSticker}"
    GET_STICKERS = "/cards/{id}/stickers"
    POST = "/cards"
    POST_ADD_LABEL = "/cards/{id}/idLabels"
    POST_ADD_MEMBER = "/cards/{id}/idMembers"
    POST_ADD_NEW_MEMBER = "/cards/{id}/labels"
    POST_ATTATCHMENTS = "/cards/{id}/attachments"
    POST_CHECKLIST = "/cards/{id}/checklists"
    POST_COMMENT = "/cards/{id}/actions/comments"
    POST_MARK_CARD_NOTIFICATION_AS_READ = "/cards/{id}/markAssociatedNotificationsRead"
    POST_MEMBER_VOTE = "/cards/{id}/membersVoted"
    POST_STICKERS = "/cards/{id}/stickers"
    PUT = "/cards/{id}"
    PUT_CHECKLIST_ITEM = "/cards/{id}/checkItem/{idCheckItem}"
    PUT_STICKER = "/cards/{id}/stickers/{idSticker}"
    PUT_UPDATE_CHECKLIST_ITEM = (
        "/cards/{idCard}/checklist/{idChecklist}/checkItem/{idCheckItem}"
    )
    PUT_UPDATE_COMMENT = "/cards/{id}/actions/{idAction}/comments"
    PUT_UPDATE_CUSTOM_FIELD = "/cards/{idCard}/customField/{idCustomField}/item"
    PUT_UPDATE_CUSTOM_FIELD_ITEMS = "/cards/{idCard}/customFields"


class Actions_Ops(Enum):
    DEL_ACTIONS = "/actions/{id}"
    DEL_REACTION = "/actions/{idAction}/reactions/{id}"
    GET_ACTIONS = "/actions/{id}"
    GET_BOARD_FOR_ACTION = "/actions/{id}/board"
    GET_CARD_FOR_ACTION = "/actions/{id}/card"
    GET_CREATOR_OF_ACTION = "/actions/{id}/memberCreator"
    GET_FIELD_ON_ACTION = "/actions/{id}/{field}"
    GET_LIST_FOR_ACTION = "/actions/{id}/list"
    GET_MEMBER_FOR_ACTION = "/actions/{id}/member"
    GET_ORGANIZATION_FOR_ACTION = "/actions/{id}/organization"
    GET_REACTIONS = "/actions/{idAction}/reactions"
    GET_REACTION_INFO = "/actions/{idAction}/reactions/{id}"
    GET_REACTION_SUMMARY = "/actions/{idAction}/reactionsSummary"
    POST_REACTION = "/actions/{idAction}/reactions"
    PUT_ACTIONS = "/actions/{id}"
    PUT_UPDATE_COMMENT = "/actions/{id}/text"


class Req_Type(Enum):
    UNSET = "UNSET"
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass(kw_only=True, repr=False)
class TrCreds:
    api_key: str
    api_token: str


async def async_trello_req(
    req_type: Req_Type,
    url: str,
    tr_conn: TrCreds,
    query_params: dict = {},
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> httpx.Response:
    """This private method wraps Trello requests with retry logic to handle timeouts and rate limits."""
    logger.info(f"req url = {url}")
    params = query_params or {}
    params["key"] = tr_conn.api_key
    params["token"] = tr_conn.api_token

    req_content = {
        "method": req_type.value,
        "url": url,
        "headers": HEADERS,
        "params": params,
        "timeout": 30,  # Set a reasonable timeout (e.g., 30 seconds)
    }

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response: httpx.Response = await client.request(**req_content)

            if response.status_code == 200:
                logger.success(
                    f"Request at {url} finished successfully. {response.status_code=}"
                )
                return response
            if response.status_code in {423, 429}:
                retry_after = response.headers.get("retry-after")
                if retry_after:
                    logger.warning(
                        f"Rate limit hit. Retrying in {retry_after} seconds..."
                    )
                    await asyncio.sleep(float(retry_after))
                else:
                    logger.warning(
                        "Rate limit hit but no 'retry-after' header found. Using backoff factor."
                    )
                    await asyncio.sleep(backoff_factor * (2**attempt))
            elif response.status_code == 504:
                logger.error(f"Timeout at {url}. Retrying...")
            else:
                response.raise_for_status()
                return response
        # except httpx.RequestError as e:
        # logger.error(f"Request error: {e}. \n {req_content:} \n Retrying...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Retrying...")

    raise Exception(f"Max retries exceeded for request at {url} with params: {params}")


async def get_lists_with_board_id(
    board_id: str,
    tr_conn: TrCreds,
    params: dict = {},
) -> httpx.Response:
    """Get lists from board"""
    url = BASE_URL + Board_Ops.GET_LISTS_ON_BOARD.value.format(id=board_id)
    return await async_trello_req(
        req_type=Req_Type.GET,
        url=url,
        query_params=params,
        tr_conn=tr_conn,
    )


async def get_boards_from_org(
    tr_conn: TrCreds,
    params: dict = {},
) -> httpx.Response:
    """Get boards from org"""
    url = ORG_URL + "/boards"
    return await async_trello_req(
        req_type=Req_Type.GET,
        url=url,
        query_params=params,
        tr_conn=tr_conn,
    )


async def get_board_with_id(
    board_id: str,
    tr_conn: TrCreds,
    params: dict = {},
) -> httpx.Response:
    """Get board from id"""
    url = BASE_URL + Board_Ops.GET_BOARD.value.format(id=board_id)
    return await async_trello_req(
        req_type=Req_Type.GET,
        url=url,
        query_params=params,
        tr_conn=tr_conn,
    )


async def get_custom_fields_with_board_id(
    board_id: str,
    tr_conn: TrCreds,
    params: dict = {},
) -> httpx.Response:
    """Get custom fields from board"""
    url = BASE_URL + Board_Ops.GET_GET_CUSTOM_FIELDS_ON_BOARD.value.format(id=board_id)
    return await async_trello_req(
        req_type=Req_Type.GET,
        url=url,
        query_params=params,
        tr_conn=tr_conn,
    )


async def get_board_members_with_board_id(
    board_id: str,
    tr_conn: TrCreds,
    params: dict = {},
) -> httpx.Response:
    """Get board members from board"""
    url = BASE_URL + Board_Ops.GET_MEMBERS_ON_BOARD.value.format(id=board_id)
    return await async_trello_req(
        req_type=Req_Type.GET,
        url=url,
        query_params=params,
        tr_conn=tr_conn,
    )


async def get_actions_with_card_id(
    card_id: str,
    tr_conn: TrCreds,
    params: dict = {},
) -> httpx.Response:
    """Get actions from card"""
    url = BASE_URL + Card_Ops.GET_ATIONS.value.format(id=card_id)
    return await async_trello_req(
        req_type=Req_Type.GET,
        url=url,
        query_params=params,
        tr_conn=tr_conn,
    )
