from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from itertools import chain

import polars as pl
from loguru import logger

from .job import Job
from .quote import Quote


@dataclass
class Raw_Project:
    """Project class to hold all the jobs in a project and generate useful information from them"""

    name: str
    jobs: list[Job]
    shared_drains: bool

    @cached_property
    def job_names(self) -> list[str]:
        return [i.name for i in self.jobs]

    @cached_property
    def job_ids(self) -> list[str]:
        return [i.id for i in self.jobs]

    @cached_property
    def project_manager(self) -> str | None:
        try:
            pm_list = [i.project_manager for i in self.jobs]
            pm = next((i for i in pm_list if i is not None), None)
        except AttributeError:
            pm = None
        return pm

    @cached_property
    def surveyed_by(self) -> str | None:
        try:
            sb_list = [i.surveyed_by for i in self.jobs]
            sb = next((i for i in sb_list if i is not None), None)
        except AttributeError:
            sb = None
        return sb

    @cached_property
    def eqc_claim_manager(self) -> str | None:
        try:
            eqc_list = [i.eqc_claim_manager for i in self.jobs]
            eqc = next((i for i in eqc_list if i is not None), None)
        except AttributeError:
            eqc = None
        return eqc

    @cached_property
    def report_by(self) -> str | None:
        try:
            rb_list = [i.report_by for i in self.jobs]
            rb = next((i for i in rb_list if i is not None), None)
        except AttributeError:
            rb = None
        return rb

    @cached_property
    def assigned_to(self) -> str | None:
        try:
            ja_list = [i.job_assigned_to for i in self.jobs]
            ja = next((i for i in ja_list if i is not None), None)
        except AttributeError:
            ja = None
        return ja

    @cached_property
    def concreter(self) -> str | None:
        try:
            conc_list = [i.concreter for i in self.jobs]
            conc = next((i for i in conc_list if i is not None), None)
        except AttributeError:
            conc = None
        return conc

    @cached_property
    def statuses(self) -> list[str]:
        return list(set([i.status for i in self.jobs]))

    @cached_property
    def job_cards_urls(self) -> list[str]:
        return list(set([i.url for i in self.jobs]))

    @cached_property
    def labour_hours(self) -> float | None:
        hours = 0
        for i in self.jobs:
            if i.labour_hours is not None:
                hours += i.labour_hours
        return round(hours, 2)

    @cached_property
    def site_staff(self) -> Sequence[str] | None:
        site_staff = []
        for i in self.jobs:
            if i.site_staff is not None:
                for j in i.site_staff:
                    site_staff.append(j)
        return list(set(site_staff))

    @cached_property
    def labour_records(self) -> Mapping[str, dict | None] | None:
        labour_record = {}
        for i in self.jobs:
            if i.labour_records is not None:
                labour_record[i.name] = i.labour_records
        return labour_record

    @cached_property
    def timeline(self) -> Mapping[str, Sequence[Mapping[str, datetime]]]:
        timeline = {}
        for i in self.jobs:
            if i.timeline is not None:
                timeline[i.name] = i.timeline
        return timeline

    @cached_property
    def customer_details(self) -> Mapping[str, dict | None] | None:
        customer_details = {}
        for i in self.jobs:
            if i.customer_details is not None:
                customer_details[i.name] = i.customer_details
        return customer_details

    @cached_property
    def qty_from_cards(self) -> Mapping[str, Mapping[str, float | None]]:
        qty_from_cards = {}
        for i in self.jobs:
            if i.qty_from_card is not None:
                qty_from_cards[i.name] = i.qty_from_card
        return qty_from_cards

    @cached_property
    def sum_qty_from_cards(self) -> Mapping[str, float | None] | None:
        sum_qty_from_cards = {}
        if self.qty_from_cards is not None:
            for v in self.qty_from_cards.values():
                for key, value in v.items():
                    if key not in sum_qty_from_cards:
                        if value is not None:
                            sum_qty_from_cards[key] = value
                    elif value is not None:
                        try:
                            sum_qty_from_cards[key] += value
                        except TypeError:
                            logger.warning(
                                f"adding {value} to {sum_qty_from_cards[key]} for {key} failed",
                            )

        return sum_qty_from_cards

    @cached_property
    def quotes(self) -> list[Quote]:
        return list(chain.from_iterable([i.quotes for i in self.jobs]))

    @cached_property
    def quote_nos(self) -> list[str]:
        return [quote.quote_no for quote in self.quotes]

    @cached_property
    def variation_quotes(self) -> list[Quote]:
        return list(chain.from_iterable([i.variation_quotes for i in self.jobs]))

    @cached_property
    def variation_quote_nos(self) -> list[str]:
        return [quote.quote_no for quote in self.variation_quotes]

    @cached_property
    def merged_quotes(self) -> Quote | None:
        """Merge all the q"""
        if self.quotes == []:
            return None
        from enviroflow_app.elt.transform.from_quotes import From_Quotes_List

        merged = From_Quotes_List(self.quotes).merge_quotes(self.name)
        # if self.variation_quotes is not [] and self.variation_quotes is not None:
        #     to_merge = self.variation_quotes.append(merged)
        #     merged = From_Quotes_List(to_merge).merge_quotes(self.name)
        return merged

    @cached_property
    def dict_for_persist(self) -> dict:
        project_dict = {
            "name": self.name,
            "shared_drains": self.shared_drains,
            "job_names": self.job_names,
            "job_ids": self.job_ids,
            "statuses": self.statuses,
            "job_cards_urls": self.job_cards_urls,
            "surveyed_by": self.surveyed_by,
            "report_by": self.report_by,
            "eqc_claim_manager": self.eqc_claim_manager,
            "project_manager": self.project_manager,
            "assigned_to": self.assigned_to,
            "site_staff": self.site_staff,
            "concreter": self.concreter,
            "labour_hours": self.labour_hours,
            "quote_nos": self.quote_nos,
            "variation_quote_nos": self.variation_quote_nos,
            # Below are the data structures thar caused trouble when duckdb infferred types. they are stringifyied, and will unpack with literal eval at the other end.
            "customer_details": str(self.customer_details),
            "qty_from_cards": str(self.qty_from_cards),
            "timeline": str(self.timeline),
            "labour_records": str(self.labour_records),
            "sum_qty_from_cards": str(self.sum_qty_from_cards),
        }
        return project_dict


@dataclass
class Project:
    name: str
    job_names: str = field(repr=False)
    shared_drains: bool
    statuses: list[str]
    job_cards_urls: list[str] = field(repr=False)
    job_ids: list[str] = field(repr=False)
    surveyed_by: str | None
    report_by: str | None
    eqc_claim_manager: str | None = field(repr=False)
    project_manager: str | None
    assigned_to: str | None

    site_staff: list[str]
    concreter: str | None = field(repr=False)
    labour_hours: float = field(repr=False)
    quote_nos: list[str] | None
    variation_quote_nos: list[str] | None
    customer_details: Mapping[str, dict | None] | None = field(repr=False)
    qty_from_cards: Mapping[str, Mapping[str, float | None]] = field(repr=False)
    timeline: Mapping[str, Sequence[Mapping[str, datetime]]]
    labour_records: Mapping[str, Mapping[str, float | None]] = field(repr=False)
    sum_qty_from_cards: Mapping[str, float | None] = field(repr=False)

    # ==From Other Sources==
    jobs: list[Job] | None = field(default=None)
    quotes: list[Quote] | None = field(default=None)
    variation_quotes: list[Quote] | None = field(default=None)
    labour_table: pl.DataFrame | None = field(default=None)
    supplier_costs: pl.DataFrame | None = field(default=None)

    # ==Constants==
    # These are based on old numbers
    # TODO create a system to get these numbers more reliably
    LABOUR_RATE = 50.00
    EST_MARGIN = 0.4  # based on analysed jobs, build proper budget
    PROJ_OVERHEAD_AS_PCT_OF_SALES_DOLLARS = 0.12

    # ==Derived==
    @cached_property
    def xero_costs_linked(self) -> bool:
        if self.supplier_costs is not None:
            return True
        return False

    @cached_property
    def merged_quotes(self) -> Quote | None:
        """Merge all the quotes for analysis"""
        if self.quotes == [] or self.quotes is None:
            return None
        from enviroflow_app.elt.transform.from_quotes import From_Quotes_List

        quotes_to_merge = self.quotes
        if self.variation_quotes == [] or self.variation_quotes is None:
            pass
        else:
            quotes_to_merge = self.variation_quotes + quotes_to_merge
        merged_quotes = From_Quotes_List(quotes_to_merge).merge_quotes(self.name)
        return merged_quotes

    @cached_property
    def total_quote_value(self) -> float | None:
        if self.merged_quotes is not None:
            return self.merged_quotes.quote_value
        return 0

    @cached_property
    def labour_costs_total(self) -> float:
        # if self.labour_hours == 0 and self.labour_table is not None:
        #     self.labour_hours = self.labour_table["total_hours"].sum()
        labour_costs = self.labour_hours * self.LABOUR_RATE
        return round(labour_costs, 2)

    @cached_property
    def supplier_costs_total(self) -> float:
        if self.supplier_costs is not None:
            supplier_costs: pl.DataFrame = self.supplier_costs
            total_supplier_costs = supplier_costs["Gross"].sum()
            return round(total_supplier_costs, 2)
        return 0

    @cached_property
    def total_costs(self) -> float:
        total_costs = self.supplier_costs_total + self.labour_costs_total
        return round(total_costs, 2)

    @cached_property
    def gross_profit(self) -> float:
        gross_profit = self.total_quote_value - self.total_costs
        return round(gross_profit, 2)

    @cached_property
    def gp_margin_pct(self) -> float:
        if self.total_quote_value is not None and self.total_quote_value != 0:
            gp_margin = self.gross_profit / self.total_quote_value
            return round(gp_margin, 2)
        return 0

    @cached_property
    def est_proj_overhead(self) -> float:
        overhead = self.total_quote_value * self.PROJ_OVERHEAD_AS_PCT_OF_SALES_DOLLARS
        return round(overhead, 2)

    @cached_property
    def work_start(self) -> datetime | None:
        if self.labour_table is not None:
            return self.labour_table.select(pl.col("start_date").min())[0, 0]

    @cached_property
    def work_end(self) -> datetime | None:
        if self.labour_table is not None:
            return self.labour_table.select(pl.col("end_date").max())[0, 0]

    @cached_property
    def longitude(self) -> float | None:
        longitudes = []
        if self.jobs is not None:
            for i in self.jobs:
                if i.longitude is not None:
                    longitudes.append(i.longitude)
        if longitudes == []:
            return None
        return round(sum(longitudes) / len(longitudes), 2)

    @cached_property
    def latitude(self) -> float | None:
        latitudes = []
        if self.jobs is not None:
            for i in self.jobs:
                if i.latitude is not None:
                    latitudes.append(i.latitude)
        if latitudes == []:
            return None
        return round(sum(latitudes) / len(latitudes), 2)

    @cached_property
    def booking_date(self) -> datetime | None:
        booking_date = None
        if self.jobs is not None:
            for i in self.jobs:
                if i.timeline["original_booking_date"] is not None:
                    booking_date = i.timeline["original_booking_date"]
        return booking_date

    @cached_property
    def dict_for_persist(self) -> dict:
        project_dict = {
            "name": self.name,
            "job_names": self.job_names,
            "shared_drains": self.shared_drains,
            "statuses": self.statuses,
            "original_booking_date": self.booking_date,
            "surveyed_by": self.surveyed_by,
            "report_by": self.report_by,
            "eqc_claim_manager": self.eqc_claim_manager,
            "total_quote_value": self.total_quote_value,
            "project_manager": self.project_manager,
            "assigned_to": self.assigned_to,
            "site_staff": self.site_staff,
            "concreter": self.concreter,
            "labour_hours": self.labour_hours,
            "labour_cost_total": self.labour_costs_total,
            "supplier_costs_total": self.supplier_costs_total,
            "total_costs": self.total_costs,
            "gross_profit": self.gross_profit,
            "gp_margin_pct": self.gp_margin_pct,
            "est_proj_overhead": self.est_proj_overhead,
            "job_cards_urls": self.job_cards_urls,
            "job_ids": self.job_ids,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "quote_nos": self.quote_nos,
            "variation_quote_nos": self.variation_quote_nos,
            "work_start": self.work_start,
            "work_end": self.work_end,
            # Below are the data structures thar caused trouble when duckdb infferred types. they are stringifyied, and will unpack with literal eval at the other end.
            "customer_details": str(self.customer_details),
            "qty_from_cards": str(self.qty_from_cards),
            "timeline": str(self.timeline),
            "labour_records": str(self.labour_records),
            "sum_qty_from_cards": str(self.sum_qty_from_cards),
            "xero_costs_linked": self.xero_costs_linked,
        }
        return project_dict

    # card_descrpiptions
