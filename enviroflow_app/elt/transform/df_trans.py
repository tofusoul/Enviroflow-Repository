import pandas as pd
import polars as pl
from loguru import logger

from enviroflow_app.helpers.str_helpers import clean_address_suffix

# pd.options.mode.chained_assignment = None  # default='warn'

# Common street name suffixes to remove when cleaning addresses
STREET_NAME_SUFFIXES_TO_REMOVE = [
    " Street",
    " St",
    " Road",
    " Rd",
    " Avenue",
    " Ave",
    " Drive",
    " Dr",
    " Lane",
    " Ln",
    " Place",
    " Pl",
    " Crescent",
    " Cres",
    " Close",
    " Cl",
]


def add_line_pct_to_quotes_table(quotes: pl.DataFrame) -> pl.DataFrame:
    df = quotes.to_pandas()
    line_pct = df["item"].str.extract(  # type: ignore
        r"(\d[0-9]*[.]\d[0-9]{0,3}[%])|(\d[0-9][%])",
        expand=False,
    )
    line_pct.fillna("", inplace=True)
    line_pct = (
        line_pct.iloc[:, [0, 1]]  # type: ignore
        .agg("".join, axis=1)
        .str.rstrip("%")
        .replace("", "100")
        .astype(float)
        .div(100)
        .round(3)
    )
    df.insert(3, "line_pct", line_pct)

    return pl.from_pandas(df)


def remove_columns(df: pd.DataFrame, cols_to_remove: list):
    """Remove columns with names that matches what is in the list.

    :param cols_to_remove: List[Str]
    :returns: DataFrame
    """
    df_columns = df.columns.to_list()
    new_columns = [col for col in df_columns if col not in cols_to_remove]
    return_df = df[new_columns]
    return return_df


def batch_dtypes_convert(df: pd.DataFrame, change: dict) -> pd.DataFrame:
    for dtype, column in change.items():
        if dtype == "float64" or dtype == "int64":
            assert df[column] is pd.Series
            df[column] = df[column].str.replace("", 0).astype(dtype)  # type: ignore
        if dtype == "datetime64":
            df[column] = df[column].astype(dtype)  # type: ignore
        else:
            logger.error(f"no dtype of the type {dtype} handled")
    return df


# Jobs List
def construct_full_jobs_list(
    current_jobs: pd.DataFrame,
    eqc_workflow: pd.DataFrame,
    closed_jobs: pd.DataFrame,
) -> pd.DataFrame:
    """ """
    cols_to_remove = [
        "due_complete",
        "last_update",
        "eqc_claim_number",
        "eqc_claim_manager",
        "survey_completed_on",
        "surveyed_by:",
        "surveyed_by",
        "eqc_approved_date",
        "report_sent_to_eqc",
        "sent_to_customer_date",
    ]
    cleaned_current_jobs = remove_columns(current_jobs, cols_to_remove)
    cleaned_eqc_flow = remove_columns(eqc_workflow, cols_to_remove)
    cleaned_cl_jobs = remove_columns(closed_jobs, cols_to_remove)
    # logger.info(list(cleaned_cl_jobs.columns))
    # dtypes = {
    #     "datetime64": ["due"],
    #     "float64": [
    #         "concrete_qty",
    #         "variation_value",
    #         "quote_value",
    #         "asphalt_qty",
    #         "pipelining_qty",
    #     ],
    # }
    # typed_current_jobs: pd.DataFrame = batch_dtypes_convert(
    #     cleaned_current_jobs, dtypes  # type: ignore
    # )
    # typed_eqc_workflow: pd.DataFrame = batch_dtypes_convert(cleaned_eqc_flow, dtypes)  # type: ignore
    jobs = pd.concat([cleaned_current_jobs, cleaned_eqc_flow, cleaned_cl_jobs])
    jobs["url"] = jobs["shortLink"].apply(lambda x: f"https://www.trello.com/c/{x}")
    return jobs


def clean_quotes_table(quotes: pd.DataFrame) -> pd.DataFrame:
    """Clean and create the jobs dataframe from the raw jobs dataframe"""
    return quotes


def clean_suffix(address: str) -> str:
    x = address.strip()
    for i in STREET_NAME_SUFFIXES_TO_REMOVE:
        x = x.removesuffix(i)
    return x.strip()


def clean_jobs_table(jobs: pd.DataFrame) -> pd.DataFrame:
    """This function cleans the jobs table, acceppts only well formed rows and
    returns a dictionary that groups the removed rows by the reason of for
    their removal.
    """
    # We need to remove the cards that are explicitly duplicated in the jobs process
    is_duplicate = jobs["address"].str.contains(
        "Duplicate|DUPLICATE|duplicate|DUP|dup|Dup",
    )
    dupes: pd.DataFrame = jobs[is_duplicate]  # type: ignore
    drop_dupes = jobs[~is_duplicate]
    more_than_1_comma = drop_dupes["address"].apply(lambda x: x.count(",") > 1)  # type: ignore
    melformed = drop_dupes[more_than_1_comma]
    cleaned = drop_dupes[~more_than_1_comma]
    job_names = cleaned["address"].str.split(",", expand=True)  # type: ignore
    if job_names.shape[1] == 3:
        job_names.drop(columns=job_names.columns[-1], axis=1, inplace=True)
    logger.info(job_names)
    job_names.iloc[:, 0] = job_names.iloc[:, 0].apply(clean_address_suffix)  # type: ignore
    job_names["address"] = cleaned["address"]
    address_filter = job_names.iloc[:, 0].str.contains(r"^\d{1,5}\D{1,2}")
    job_names.columns = ["job", "suburb", "address"]  # type: ignore
    job_names = job_names[address_filter]
    merged = pd.merge(job_names, cleaned)  # type :ignore

    return (merged, melformed, dupes)
