from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from enviroflow_app import config
from enviroflow_app.helpers.str_helpers import clean_address_suffix

logger.configure(**config.ELT_LOG_CONF)

DEFAULT_TIMELINE = {
    "card_due": None,
    "survey_completed_on": None,
    "sent_to_customer_date": None,
    "report_sent_to_eqc": None,
    "eqc_approved_date": None,
    "original_booking_date": None,
}

DEFAULT_CUSTOMER_DETAILS = {
    "name": None,
    "email": None,
    "phone": None,
    "second_contact": None,
}

DEFAULT_QTY_FROM_CARD = {
    "c_quote_value": 0,
    "c_variation_value": 0,
    "c_asphalt_qty": 0,
    "c_concrete_qty": 0,
    "c_pipelining_qty": 0,
}


@dataclass(kw_only=True)
class Job:
    name: str
    id: str = field(repr=False)
    status: str
    board: str = field(repr=False)
    card_title: str = field(repr=False)
    desc: str = field(repr=False)
    url: str = field(repr=False)
    address: str = field(repr=False)
    static_map_url: str = field(repr=False)
    customer_details: Mapping[str, str | None] = field(
        default_factory=lambda: DEFAULT_CUSTOMER_DETAILS,
        repr=False,
    )
    qty_from_card: Mapping[str, float | None] = field(
        default_factory=lambda: DEFAULT_QTY_FROM_CARD,
        repr=False,
    )
    timeline: Mapping[str, datetime | None] = field(
        default_factory=lambda: DEFAULT_TIMELINE,
        repr=False,
    )
    surveyed_by: str = field(repr=False)
    report_by: str = field(repr=False)
    eqc_claim_manager: str = field(repr=False)
    eqc_claim_number: str = field(repr=False)
    project_manager: str | None = field(default=None, repr=False)
    job_assigned_to: str | None = field(default=None, repr=False)
    concreter: str | None = field(default=None, repr=False)
    labels: list[tuple] = field(repr=False)
    drive_folder_link: str | list[str] | None = field(default=None, repr=False)
    linked_cards: list[dict] | None = field(default=None, repr=False)
    sorted_attatchments: dict[str, list[Any]] | None = field(default=None, repr=False)
    shared_drains: bool | None = field(default=None)
    shared_with: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
    )  # declared as Any to avoid name_error
    quote_no: str | list[str] | None = field(repr=False, default=None)
    quotes: list = field(repr=False, default_factory=list)
    variation_quotes: list = field(repr=False, default_factory=list)
    raw_attatchments: list[str] | None = field(init=False, default=None, repr=False)
    site_staff: list[str] | None = field(default=None, repr=False)
    labour_records: dict[str, float] | None = field(default=None, repr=False)
    labour_hours: float | None = field(default=None, repr=False)
    parse_notes: list[str] = field(repr=False, default_factory=list)
    longitude: float | None = field(default=None, repr=False)
    latitude: float | None = field(default=None, repr=False)

    @cached_property
    def suburb(self) -> str | None:
        if self.address is not None and "," in self.address:
            return self.address.split(", ")[1]
        return None


def build_job_from_job_card_dict(record: Mapping[str, Any]) -> Job:
    """Method to construct job form a job_card record"""
    parse_notes = []
    timeline = {
        "card_due": record["due"],
        "survey_completed_on": record["survey_completed_on"],
        "sent_to_customer_date": record["sent_to_customer_date"],
        "report_sent_to_eqc": record["report_sent_to_eqc"],
        "eqc_approved_date": record["eqc_approved_date"],
        "original_booking_date": record["original_booking_date"],
    }

    customer_details = {
        "name": record["customer_name"],
        "email": record["customer_email"],
        "phone": record["phone"],
        "second_contact": record["second_contact"],
    }

    qty_from_card = {
        "c_asphalt_qty": record["asphalt_qty"],
        "c_concrete_qty": record["concrete_qty"],
        "c_pipelining_qty": record["pipelining_qty"],
        "c_quote_value": record["quote_value"],
        "c_variation_value": record["variation_value"],
    }

    def sort_attachments(url_list: list) -> dict[str, list]:
        parsed_urls = [
            {
                "url_str": url_str,
                "netloc": urlparse(url_str).netloc,
                "path": urlparse(url_str).path,
                "query": urlparse(url_str).query,
            }
            for url_str in url_list
        ]

        sorted_urls = {
            # links sorted into these categories
            "drive_folder": [],
            "linked_cards": [],
            "pictures": [],
            "videos": [],
            "documents": [],
            "archives": [],
            "emails": [],
            "financials": [],
            "other_links": [],
        }
        for url in parsed_urls:
            match url:
                case {"netloc": "trello.com"}:
                    split_path = url["path"].split("/")
                    if split_path[-1].endswith(
                        (".jpg", ".jpeg", ".JPG", ".png", ".PNG", ".HEIC", ".heic"),
                    ):
                        sorted_urls["pictures"].append(url["url_str"])
                    elif split_path[-1].endswith(
                        (".pdf", ".PDF", ".doc", ".docx", ".xls", ".xlsx"),
                    ):
                        sorted_urls["documents"].append(url["url_str"])
                    elif split_path[-1].endswith(
                        (
                            ".zip",
                            ".rar",
                        ),
                    ):
                        sorted_urls["archives"].append(url["url_str"])
                    elif split_path[-1].endswith((".eml", ".html")):
                        sorted_urls["emails"].append(url["url_str"])
                    elif split_path[-1].endswith("noname"):
                        logger.warning("skipping noname file")
                    elif split_path[-1].endswith(
                        (".mp4", ".mov", ".xls", ".docx", ".gif"),
                    ):
                        sorted_urls["videos"].append(url["url_str"])
                    elif split_path[1] == "c":
                        sorted_urls["linked_cards"].append(url)
                    else:
                        log_str = f"Unknow trello url {url}"
                        sorted_urls["other_links"].append(url["url_str"])
                        logger.error(log_str)
                        parse_notes.append(log_str)
                case {"query": "usp=drive_link"}:
                    logger.info(f"ignoring saftety folder drive link {url['url_str']}")
                case {"netloc": "drive.google.com"}:
                    sorted_urls["drive_folder"].append(url["url_str"])
                case {"netloc": "docs.google.com"}:
                    sorted_urls["documents"].append(url["url_str"])
                case {"netloc": "mail.google.com"}:
                    sorted_urls["emails"].append(url["url_str"])
                case {"netloc": "go.xero.com"}:
                    sorted_urls["financials"].append(url["url_str"])
                case _:
                    log_str = f"{url} is not handled"
                    logger.error(log_str)
                    parse_notes.append(log_str)
                    sorted_urls["other_links"].append(url["url_str"])
                    # raise ValueError("Not a URL we are currantly have a handler for")
        return sorted_urls

    if record["attatchments"] is not None:
        sorted_attachments = sort_attachments(record["attatchments"])
        if sorted_attachments["drive_folder"] != []:
            drive_folder_link = sorted_attachments.pop("drive_folder")
        else:
            drive_folder_link = None
        linked_cards = sorted_attachments.pop("linked_cards")
    else:
        sorted_attachments = None
        drive_folder_link = None
        linked_cards = None

    if "Shared Drain" in record["labels"]:
        shared_drain = True
    else:
        shared_drain = False

    job: Job = Job(
        card_title=record["card_title"],
        name=clean_address_suffix(record["card_title"]),
        url=record["url"],
        id=record["id"],
        board=record["board"],
        status=record["status"],
        desc=record["desc"],
        address=record["address"],
        static_map_url=record["static_map_url"],
        customer_details=customer_details,
        qty_from_card=qty_from_card,
        timeline=timeline,
        surveyed_by=record["surveyed_by"],
        report_by=record["report_by"],
        eqc_claim_manager=record["eqc_claim_manager"],
        eqc_claim_number=record["eqc_claim_number"],
        project_manager=record["project_manager"],
        job_assigned_to=record["job_assigned_to"],
        concreter=record["concreter"],
        labels=record["labels"],
        drive_folder_link=drive_folder_link,
        linked_cards=linked_cards,
        sorted_attatchments=sorted_attachments,
        shared_drains=shared_drain,
        shared_with={},
        quotes=[],
        variation_quotes=[],
        parse_notes=parse_notes,
        longitude=record["coordinates"]["longitude"] if record["coordinates"] else None,
        latitude=record["coordinates"]["latitude"] if record["coordinates"] else None,
    )
    return job
