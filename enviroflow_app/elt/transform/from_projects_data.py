import ast
import datetime  # type ignore
import zoneinfo
from dataclasses import dataclass
from functools import cached_property

import polars as pl
from loguru import logger

from enviroflow_app.elt.transform.from_jobs import From_Jobs_Df
from enviroflow_app.elt.transform.from_labour_records import From_Labour_Records
from enviroflow_app.elt.transform.from_quotes import From_Quotes_Data
from enviroflow_app.helpers.str_helpers import clean_multi_address
from enviroflow_app.model import Job, Project, Quote


@dataclass(repr=False, kw_only=True)
class Projects_Data:
    projects_df: pl.DataFrame
    jobs_df: pl.DataFrame
    quotes_df: pl.DataFrame
    labour_hours_df: pl.DataFrame
    costs_df: pl.DataFrame

    @cached_property
    def cleaned_labour_hours(self) -> pl.DataFrame:
        return From_Labour_Records(self.labour_hours_df).cleaned_labour_df[0]

    @cached_property
    def quotes_dict(self) -> dict[str, Quote]:
        quotes = From_Quotes_Data(self.quotes_df).quotes_dict
        return quotes

    @cached_property
    def jobs_dict(self) -> dict[str, Job]:
        jobs = From_Jobs_Df(self.jobs_df).jobs_dict(self.quotes_dict)

        return jobs

    @cached_property
    def projects_dict(self) -> dict[str, Project]:
        def get_jobs_for_proj(job_names: list[str]) -> list[Job]:
            job_list = []
            if job_names is not None:
                for job_name in job_names:
                    if job_name in self.jobs_dict:
                        job_list.append(self.jobs_dict[job_name])
                    else:
                        logger.error(f" {job_name} not found in jobs")
            return job_list

        def get_quotes_for_jobs(
            job_list: list[Job],
            variations: bool = False,
        ) -> list[Quote]:
            quote_list = []
            if variations:
                for job in job_list:
                    if job.variation_quotes is not None:
                        for i in job.variation_quotes:
                            quote_list.append(i)
            else:
                for job in job_list:
                    for quote in job.quotes:
                        quote_list.append(quote)
            return quote_list

        def get_costs_for_project(
            df: pl.DataFrame,
            project_name: str,
            job_names: list[str],
        ) -> pl.DataFrame | None:
            if len(job_names) > 1:
                raw_name = clean_multi_address(job_names[0])
                logger.info(f"cleaning multi address: {job_names[0]} -> {raw_name}")
            else:
                raw_name = job_names[0]
            df = df.filter(
                pl.col("Project").str.contains_any(job_names)
                | pl.col("Description").str.contains_any(job_names)
                | pl.col("Project").str.contains(raw_name)
                | pl.col("Description").str.contains(raw_name),
            )
            if df.shape[0] > 0:
                filter_by_name = df.filter(pl.col("Project") == project_name)
                if filter_by_name.shape[0] > 0:
                    return filter_by_name
                return df
            return None

        def get_labour_hours_for_project(
            df: pl.DataFrame,
            job_names: list[str],
        ) -> pl.DataFrame | None:
            if len(job_names) > 1:
                raw_name = clean_multi_address(job_names[0])
                logger.info(f"cleaning multi address: {job_names[0]} -> {raw_name}")
            else:
                raw_name = job_names[0]
            df = df.filter(
                pl.col("name").str.contains_any(job_names),
                # | pl.col("name").str.contains(raw_name)
            )
            if df.shape[0] > 0:
                return df
            return None

        raw_projs = {proj["name"]: proj for proj in self.projects_df.to_dicts()}

        for proj in raw_projs.values():
            proj["customer_details"] = ast.literal_eval(proj["customer_details"])
            proj["qty_from_cards"] = ast.literal_eval(proj["qty_from_cards"])
            # Create safe eval context with required imports
            eval_context = {
                "datetime": datetime,
                "zoneinfo": zoneinfo,
                "__builtins__": {},
            }
            proj["timeline"] = eval(proj["timeline"], eval_context)
            # TODO above is Very unsafe, FIX! see https://stackoverflow.com/questions/4235606/way-to-use-ast-literal-eval-to-convert-string-into-a-datetime for tips
            proj["labour_records"] = ast.literal_eval(proj["labour_records"])
            proj["sum_qty_from_cards"] = ast.literal_eval(proj["sum_qty_from_cards"])
            proj["jobs"] = get_jobs_for_proj(proj["job_names"])
            proj["quotes"] = get_quotes_for_jobs(proj["jobs"])
            proj["variation_quotes"] = get_quotes_for_jobs(
                proj["jobs"],
                variations=True,
            )
            proj["supplier_costs"] = get_costs_for_project(
                self.costs_df,
                proj["name"],
                proj["job_names"],
            )
            proj["labour_table"] = get_labour_hours_for_project(
                self.cleaned_labour_hours,
                proj["job_names"],
            )

        proj_dict = {name: Project(**proj) for name, proj in raw_projs.items()}

        return proj_dict


print(type(datetime))
