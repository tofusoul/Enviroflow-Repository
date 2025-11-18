from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property

import polars as pl
from loguru import logger

from enviroflow_app import config
from enviroflow_app.model.quote import Quote

logger.configure(**config.ELT_LOG_CONF)


@dataclass
class From_Quotes_Data:
    quotes_df: pl.DataFrame = field(repr=False)

    @cached_property
    def quote_nos(self) -> list[str]:
        return self.quotes_df["quote_no"].unique().to_list()

    @cached_property
    def quotes_dict(self) -> dict[str, Quote]:
        """Returns a dictionary with quote numer as key and quote object as value"""
        quotes_dict = {}
        for i in self.quote_nos:
            quote_df = self.quotes_df.filter(pl.col("quote_no") == i)
            quote = Quote(
                quote_no=i,
                quote_ref=quote_df["quote_ref"].unique().item(0),
                quote_status=quote_df["quote_status"].unique().item(0),
                created=quote_df["created"].unique().item(0),
                quote_source=quote_df["quote_source"].unique().item(0),
                quote_lines=quote_df.select(
                    [
                        "quote_no",
                        "item_desc",
                        "item_code",
                        "line_pct",
                        "quantity",
                        "unit_price",
                        "line_total",
                    ],
                ),
                quote_value=round(quote_df["line_total"].sum(), 2),
            )
            quotes_dict[i] = quote
        return quotes_dict

    @cached_property
    def jobs2quotes_map(self) -> dict[str, Quote]:
        """Returns a dictioanry with job name as key and quote object as value"""
        jobs2quotes = {}
        for q in self.quotes_dict.values():
            if q.quote_ref is None:
                jobs2quotes[q.quote_no] = q
            else:
                jobs2quotes[q.quote_ref] = q

        return jobs2quotes


@dataclass(repr=False)
class From_Quotes_List:
    quotes: list[Quote] = field(repr=False)

    def merge_quotes(self, name: str) -> Quote:
        """If the quote list has multiple quotes, merge the quotes and into one dataframe,
        else return the quote
        """
        for i in self.quotes:
            if i is None:
                self.quotes.remove(i)

        dfs = []
        for i in self.quotes:
            dfs.append(i.quote_lines)

        try:
            df = pl.concat(dfs)
            quote_value = df["line_total"].sum()
        except ValueError:
            logger.error(f"couldn't concatenate quote for {name} ")
            df = pl.DataFrame()
            quote_value = 0
        merged_quotes = Quote(
            quote_lines=df,
            quote_no="various",
            quote_status="derived",
            created=datetime.now(),
            quote_ref=name,
            quote_source="merged",
            quote_value=round(quote_value, 2),
        )
        return merged_quotes
