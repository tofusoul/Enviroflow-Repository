import re
from dataclasses import dataclass
from functools import cached_property
from typing import NamedTuple, Tuple

import polars as pl
from loguru import logger

from enviroflow_app import config
from enviroflow_app.helpers.str_helpers import clean_address_suffix
from enviroflow_app.model import Job, Quote
from enviroflow_app.model.job import build_job_from_job_card_dict

logger.configure(**config.ELT_LOG_CONF)


class Job_Parse_Results(NamedTuple):
    jobs: dict[str, Job]
    no_quotes_matched: dict[str, Job]
    attatched_card_not_parsed: list[dict[str, str]]
    removed_cards: pl.DataFrame


@dataclass(repr=False)
class From_Job_Cards:
    job_cards: pl.DataFrame

    @cached_property
    def customers_dict(self) -> dict[str, dict]:
        """"""
        customer_records = self.job_cards.select(
            pl.col("customer_name").alias("name"),
            pl.col("customer_email").alias("email"),
            pl.col("phone"),
            pl.col("card_title").alias("job_name"),
        ).to_dicts()

        customers: dict[str, dict] = {}
        for c in customer_records:
            if c["name"] not in customers:
                customers[c["name"]] = c
                customers[c["name"]]["job_names"] = [c["job_name"]]
                del customers[c["name"]]["job_name"]
            else:
                customers[c["name"]]["job_names"].append(c["job_name"])

        return customers

    @cached_property
    def customers_df(self) -> pl.DataFrame:
        return pl.from_dicts(list(self.customers_dict.values()))

    @cached_property
    def clean_job_cards(self) -> Tuple[pl.DataFrame, pl.DataFrame]:
        """Prepare and clean the job cards info to be parsed into the more usable job objects"""
        TO_DROP = [
            "digger_type",
            "due_complete",
            "exposed_ag_concrete",
            "exposed_aggregate",
            "pipeline_patch_required",
        ]
        TO_RENAME = {
            "card_id": "long_id",
            "short_url": "id",
            "scheduled_date_week_beginning": "original_booking_date",
            "board_name": "board",
        }

        df = self.job_cards.drop(TO_DROP)
        df = df.rename(TO_RENAME)

        marked_duplicate = pl.col("card_title").str.contains(
            "Duplicate|DUPLICATE|duplicate|DUP|dup|Dup",
        )
        is_job = pl.col("card_title").str.contains(r"^\d")
        removed = df.filter(marked_duplicate | ~is_job)
        cleaned = df.join(removed, on=["id", "card_title"], how="anti")

        return cleaned, removed

    def build_jobs_dict(self, jobs2quotes_map: dict[str, Quote]) -> Job_Parse_Results:
        """Builds dictionaries of job objects for each job_card in the interim dataframe
        from quotes map and job cards, returns:

        """
        jobs = {}
        job_has_no_matched_quotes = {}
        job_cards_dict = self.clean_job_cards[0].to_dicts()
        removed_cards = self.clean_job_cards[1]
        id2name = {
            i["id"]: clean_address_suffix(i["card_title"]) for i in job_cards_dict
        }
        for card in job_cards_dict:
            job: Job = build_job_from_job_card_dict(card)
            pattern = rf"(^|\W){re.escape(job.name.lower())}(\W|$)"
            for job_name, quote in jobs2quotes_map.items():
                # if job.name.lower() in job_name.lower():
                if re.search(pattern, job_name.lower()):
                    if "variation" in job_name.lower() or "private" in job_name.lower():
                        logger.info(
                            f"found variation quote {quote.quote_no} for {job.name}",
                        )
                        job.variation_quotes.append(quote)
                    else:
                        logger.info(f"found quote {quote.quote_no} for {job.name}")
                        job.quotes.append(quote)

            if (
                job.quotes == []
                and job.status != "NFA, No Damage, PVC"
                and job.board != "Survey Workflow"
            ):
                logger.warning(f"no quotes found for {job.name}, status = {job.status}")
                job_has_no_matched_quotes[job.name] = job

            jobs[job.name] = job

        attatched_card_not_on_board = []
        for job_name, job in jobs.items():
            if job.linked_cards is None:
                if job.shared_drains:
                    log_msg = f"job {job_name} has shared drain but no linked cards"
                    job.parse_notes.append(log_msg)
                    logger.error(log_msg)
            else:
                for card in job.linked_cards:
                    id = card["path"].split("/")[2]
                    try:
                        shared_target_name = id2name[id]
                        logger.info(f"{job_name} shared with {shared_target_name}")
                        job.shared_with[shared_target_name] = jobs[shared_target_name]
                    except KeyError:
                        log_msg = f"attatched card with {id} at {card['url_str']} is not a parsed job card"
                        logger.error(log_msg)
                        attatched_card_not_on_board.append(
                            {
                                "card": job.name,
                                "card_url": job.url,
                                "card_attachment_not_job": card["url_str"],
                            },
                        )
                        job.parse_notes.append(log_msg)

        result = Job_Parse_Results(
            jobs=jobs,
            no_quotes_matched=job_has_no_matched_quotes,
            attatched_card_not_parsed=attatched_card_not_on_board,
            removed_cards=removed_cards,
        )
        return result
