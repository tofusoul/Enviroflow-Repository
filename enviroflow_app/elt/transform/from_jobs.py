"""ops to and from jobs dict"""

from dataclasses import dataclass
from functools import cached_property

import polars as pl
from loguru import logger

from enviroflow_app import config
from enviroflow_app.model import Job, Quote

logger.configure(**config.ELT_LOG_CONF)


@dataclass(repr=False)
class From_Jobs_Dict:
    jobs: dict[str, Job]

    @cached_property
    def jobs_df(self) -> pl.DataFrame:
        job_records = [
            {
                "name": job.name,
                "id": job.id,
                "status": job.status,
                "board": job.board,
                "suburb": job.suburb,
                "card_title": job.card_title,
                "url": job.url,
                "address": job.address,
                "customer_details": job.customer_details,
                "qty_from_card": job.qty_from_card,
                "timeline": job.timeline,
                "surveyed_by": job.surveyed_by,
                "desc": job.desc,
                "static_map_url": job.static_map_url,
                "report_by": job.report_by,
                "eqc_claim_manager": job.eqc_claim_manager,
                "eqc_claim_number": job.eqc_claim_number,
                "project_manager": job.project_manager,
                "job_assigned_to": job.job_assigned_to,
                "concreter": job.concreter,
                "labels": job.labels,
                "drive_folder_link": job.drive_folder_link,
                "linked_cards": [card["url_str"] for card in job.linked_cards]
                if job.linked_cards
                else None,
                "sorted_attatchments": job.sorted_attatchments,
                "shared_drains": job.shared_drains,
                "shared_with": [k for k in job.shared_with.keys()],
                "quotes": [q.quote_no for q in job.quotes],
                "variation_quotes": [q.quote_no for q in job.variation_quotes],
                "parse_notes": job.parse_notes,
                "longitude": job.longitude,
                "latitude": job.latitude,
            }
            for job in self.jobs.values()
        ]
        return pl.from_dicts(job_records, infer_schema_length=100000)


@dataclass(repr=False)
class From_Jobs_Df:
    jobs_df: pl.DataFrame

    def jobs_dict(self, quotes: dict[str, Quote]) -> dict[str, Job]:
        records = self.jobs_df.to_dicts()
        jobs = {}
        share_match = {}
        quotes_match = {}
        variation_quotes_match = {}
        for job_record in records:
            name = job_record["name"]
            jobs[name] = Job(
                name=job_record["name"],
                id=job_record["id"],
                status=job_record["status"],
                board=job_record["board"],
                card_title=job_record["card_title"],
                url=job_record["url"],
                desc=job_record["desc"],
                address=job_record["address"],
                static_map_url=job_record["static_map_url"],
                customer_details=job_record["customer_details"],
                qty_from_card=job_record["qty_from_card"],
                timeline=job_record["timeline"],
                surveyed_by=job_record["surveyed_by"],
                report_by=job_record["report_by"],
                eqc_claim_manager=job_record["eqc_claim_manager"],
                eqc_claim_number=job_record["eqc_claim_number"],
                project_manager=job_record["project_manager"],
                job_assigned_to=job_record["job_assigned_to"],
                concreter=job_record["concreter"],
                labels=job_record["labels"],
                drive_folder_link=job_record["drive_folder_link"],
                linked_cards=job_record["linked_cards"],
                sorted_attatchments=job_record["sorted_attatchments"],
                shared_drains=job_record["shared_drains"],
                parse_notes=job_record["parse_notes"],
                longitude=job_record["longitude"],
                latitude=job_record["latitude"],
            )
            try:
                jobs[name].site_staff = job_record["site_staff"]
            except KeyError:
                logger.warning(f"no staff found for {job_record['name']}")

            try:
                jobs[name].labour_records = job_record["labour_records"]
            except KeyError:
                logger.warning(f"no labour records found for {job_record['name']}")

            try:
                jobs[name].labour_hours = job_record["labour_hours"]
            except KeyError:
                logger.warning(f"no labour hours found for {job_record['name']}")

            share_match[name] = job_record["shared_with"]
            quotes_match[name] = job_record["quotes"]
            variation_quotes_match[name] = job_record["variation_quotes"]

        for job_record, shared_with in share_match.items():
            jobs[job_record].shared_with = {j: jobs[j] for j in shared_with}

        for job_record, quotes_list in quotes_match.items():
            try:
                jobs[job_record].quotes = [quotes[q] for q in quotes_list]
            except KeyError as e:
                logger.error(f"quote no. {e} not found")

        for job_record, quotes_list in variation_quotes_match.items():
            try:
                jobs[job_record].variation_quotes = [quotes[q] for q in quotes_list]
            except KeyError as e:
                logger.error(f"variation qquote no. {e} not found")

        return jobs
