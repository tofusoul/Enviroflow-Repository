"""this module includes functions that brings table together on the server"""

import polars as pl

from enviroflow_app.elt.motherduck import md


def normalise_xero_quotes(xero_quotes: pl.DataFrame) -> pl.DataFrame:
    return xero_quotes.drop(
        [
            "__index_level_0__",
            "updated",
            "quote_id",
            "line_id",
            "contact_id",
        ],
    ).select(
        pl.col("quote_no"),
        pl.col("quote_ref"),
        pl.col("customer"),
        pl.col("quote_status"),
        pl.col("item_desc"),
        pl.col("item_code"),
        pl.col("line_pct"),
        pl.col("quantity"),
        pl.col("unit_price"),
        pl.col("line_total"),
        pl.col("created").cast(pl.Date),
        pl.lit("Xero").alias("quote_source"),
    )


def normalise_simpro_quotes(simpro_quotes: pl.DataFrame) -> pl.DataFrame:
    return (
        simpro_quotes.drop(["quote_total", "date_approved"])
        .rename(
            {
                "site": "quote_ref",
                "customer": "customer",
                "date_created": "created",
                "item": "item_desc",
                "unit_price": "unit_price",
                "total": "line_total",
            },
        )
        .select(
            pl.col("quote_no"),
            pl.col("quote_ref"),
            pl.col("customer"),
            pl.lit("").alias("quote_status"),
            pl.col("item_desc"),
            pl.lit("").alias("item_code"),
            pl.col("line_pct"),
            pl.col("quantity"),
            pl.col("unit_price"),
            pl.col("line_total"),
            pl.col("created"),
            pl.col("quote_source"),
        )
    )


def stitch_quotes_on_md(conn: md.MotherDuck) -> pl.DataFrame:
    """Stiches"""
    simpro_quotes = normalise_simpro_quotes(conn.get_table("full_simpro_quotes"))
    xero_quotes = normalise_xero_quotes(conn.get_table("full_xero_quotes"))
    quotes = (
        pl.concat([simpro_quotes, xero_quotes])
        # below fix a weird problem with parsing percentages
        .with_columns(
            pl.when(pl.col("line_pct") == 0)
            .then(1)
            .otherwise(pl.col("line_pct"))
            .alias("line_pct"),
        )
    )
    conn.save_table("quotes", quotes)
    return quotes


def update_items_budget_table(conn: md.MotherDuck) -> None:
    """Updates the used"""
    with open("enviroflow_app/db_queries/update_item_budget_table.sql") as sql:
        sql_str = sql.read()
        conn.run_sql(sql_str)
