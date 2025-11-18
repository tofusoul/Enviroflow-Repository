from typing import Tuple

import polars as pl
from helpers.str_helpers import clean_address_suffix


def add_hours(
    jobs_df: pl.DataFrame, labour_df: pl.DataFrame
) -> Tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    exclude_employee = [
        "Dave",
        "Pat",
        "Rodolfo Sueta",
        "D4 Drains",
        "MHR",
        "NZ Drains",
        "Haase Marshall",
    ]

    df = labour_df.filter(
        ~pl.col("employee").is_in(exclude_employee)
        & pl.col("name").str.contains(r"^\d"),
    )
    removed = labour_df.filter(
        pl.col("employee").is_in(exclude_employee)
        & ~pl.col("name").str.contains(r"^\d"),
    )
    df = df.with_columns(
        pl.col("name").apply(clean_address_suffix, return_dtype=pl.Utf8),
    )
    aggregated_df = df.groupby("name").agg(
        [
            pl.sum("total_hours"),
            pl.col("employee").unique().alias("employees_list"),
            pl.struct(["employee", "total_hours"])
            .apply(
                lambda x: {item["employee"]: item["total_hours"] for item in x},
                return_dtype=pl.Object,
            )
            .alias("employee_hours_dict"),
        ],
    )
    result_df = jobs_df.join(aggregated_df, on="name", how="left")
    return result_df, aggregated_df, removed


#
# # Add 'clean_name' field in the labour_hours_df by matching substrings
# labour_hours_df = labour_hours_df.with_column(
#     pl.col('name').apply(lambda x: next((job for job in jobs_df['clean_name'] if job in x), None)).alias('clean_name')
# )
#
# # Group by 'clean_name' to calculate the total hours and employee details
# aggregated_df = labour_hours_df.groupby('clean_name').agg([
#     pl.sum('hours').alias('total_hours'),
#     pl.list('employee').alias('employees_list'),
#     pl.col('employee').unique().apply(lambda employees: {employee: labour_hours_df.filter(pl.col('employee') == employee)['hours'].sum() for employee in employees}).alias('employee_hours_dict')
# ])
#
# # Join the aggregated data with the jobs_df
# result_df = jobs_df.join(aggregated_df, on='clean_name', how='left')
#
# # Select the required columns
# result_df = result_df.select(['name', 'total_hours', 'employees_list', 'employee_hours_dict'])
#
