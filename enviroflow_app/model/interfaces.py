from typing import Protocol

import polars as pl


class Table_Store(Protocol):
    def get_table(self, table_name: str) -> pl.DataFrame:
        pass

    def save_table(self, table_name: str, table: pl.DataFrame) -> None:
        pass

    def get_table_list(self) -> list[str]:
        pass
