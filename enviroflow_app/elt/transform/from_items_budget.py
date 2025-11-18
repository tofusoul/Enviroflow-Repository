from dataclasses import dataclass

import polars as pl


@dataclass
class From_Items_Budget:
    item_budget_df: pl.DataFrame

    def budgeted_quotes(self, quotes: pl.DataFrame) -> pl.DataFrame:
        return_df = quotes

        return return_df
