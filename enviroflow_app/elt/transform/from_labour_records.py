from dataclasses import dataclass
from functools import cached_property
from typing import NamedTuple, Tuple

import polars as pl
from loguru import logger

from enviroflow_app import config

logger.configure(**config.ELT_LOG_CONF)
from enviroflow_app.helpers.str_helpers import clean_address_suffix


class Jobs_With_Labour_Results(NamedTuple):
    jobs_df: pl.DataFrame
    aggregated_df: pl.DataFrame
    removed: pl.DataFrame
    job_no_hour_data: pl.DataFrame


@dataclass(repr=False)
class From_Labour_Records:
    labour_records: pl.DataFrame

    @cached_property
    def cleaned_labour_df(self) -> Tuple[pl.DataFrame, pl.DataFrame]:
        EXCLUDE_EMPLOYEE = [
            "Dave",
            "Pat",
            "Rodolfo Sueta",
            # "D4 Drains",
            # "MHR",
            # "NZ Drains",
            # "Haase Marshall",
        ]

        df = self.labour_records.filter(
            ~pl.col("employee").is_in(EXCLUDE_EMPLOYEE)
            & pl.col("name").str.contains(r"^\d"),
        )
        removed = self.labour_records.filter(
            pl.col("employee").is_in(EXCLUDE_EMPLOYEE)
            & ~pl.col("name").str.contains(r"^\d"),
        )
        df = df.with_columns(
            pl.col("name").map_elements(clean_address_suffix, return_dtype=pl.String),
        )

        return df, removed

    @cached_property
    def agg_hours(self) -> Tuple[pl.DataFrame, pl.DataFrame]:
        removed = self.cleaned_labour_df[1]
        aggregated_df = (
            self.cleaned_labour_df[0]
            .group_by("name")
            .agg(
                [
                    pl.sum("total_hours").alias("labour_hours"),
                    pl.col("employee").unique().alias("site_staff"),
                    # Create a simplified labour records structure
                    pl.struct(["employee", "total_hours"])
                    .map_elements(
                        lambda x: str(x),  # Simple string representation for now
                        return_dtype=pl.String,
                    )
                    .alias("labour_records"),
                ],
            )
        )

        return aggregated_df, removed

    def jobs_with_labour(self, jobs_df: pl.DataFrame) -> Jobs_With_Labour_Results:
        aggregated_df, removed = self.agg_hours
        jobs_df = jobs_df.join(aggregated_df, on="name", how="left")
        jobs_with_no_hour_data = jobs_df.filter(pl.col("labour_hours").is_null())
        return Jobs_With_Labour_Results(
            jobs_df=jobs_df,
            aggregated_df=aggregated_df,
            removed=removed,
            job_no_hour_data=jobs_with_no_hour_data,
        )
