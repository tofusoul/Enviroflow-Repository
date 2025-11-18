from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple

import config
import polars as pl
from loguru import logger

logger.configure(**config.ELT_LOG_CONF)


@dataclass
class Sales_Item:
    code: str
    name: str = field(repr=False)
    sell_price: float
    unit_of_measure: str = field(repr=False)
    labour_hours_per_unit: float = field(repr=False)
    labour_cost_per_unit: float = field(repr=False)
    supplier_costs_per_unit: float = field(repr=False)
    total_cost_per_unit: float
    margin: float = field(repr=False)
    cost_pct: float = field(repr=False)
    margin_pct: float = field(repr=False)
    to_update_in_xero: bool = field(repr=False)
    has_cost_buildup: bool | None = field(repr=False, default=None)
    buildup_needs_attention: bool = field(repr=False, default=False)
    cost_buildup: pl.DataFrame | None = None
    last_update: datetime | None = None
    notes: str | None = field(repr=False, default=None)
    url: str | None = field(repr=False, default=None)


def build_sales_items_from_tables(
    items_budget: pl.DataFrame, cost_calcs: pl.DataFrame
) -> dict[str, Sales_Item]:
    sales_items = {}
    for i in items_budget.to_dicts():
        sales_items[i["code"]] = Sales_Item(**i)
        try:
            sales_items[i["code"]].cost_buildup = cost_calcs.filter(
                pl.col("xero_code") == i["code"]
            )
        except Exception as e:
            logger.warning(f"no cost buildup for {i['code']}, {e}")
    return sales_items


def build_sales_buildup_table_from_object(
    sales_items: list[Sales_Item],
) -> Tuple[pl.DataFrame, pl.DataFrame]:
    pass
