from dataclasses import dataclass
from functools import cached_property

import pandas as pd
import polars as pl


@dataclass
class From_Subs_Rates:
    rates: pl.DataFrame
    sub_name: str

    @cached_property
    def rates_dict(self) -> dict[str, int | float]:
        keys = [
            "se",
            "asbuilt",
            "ss",
            "sw",
            "sssw",
            "gully",
            "bub",
            "cap_sewer",
            "drive_sump",
            "channel_drain",
            "hardfill",
            "concrete",
            "concut",
            "asphalt",
            "deck",
            "gravel",
            "pavers_not_in_concrete",
            "pavers_in_concrete",
            "bush",
            "bark_mulch",
            "bark_nugget",
            "clothes_line",
            "fence",
            "weed_mat",
            "hydroseed",
            "stones_on_mat",
            "add_lab",
            "gas",
            "watermain",
        ]
        rates: dict = {}
        df: pd.DataFrame = self.rates.to_pandas()  # type: ignore
        for i in keys:
            rates[i] = (
                df.loc[df["lookup_code"] == i, self.sub_name]
                .reset_index(drop=True)
                .iloc[0]
            )
        return rates
