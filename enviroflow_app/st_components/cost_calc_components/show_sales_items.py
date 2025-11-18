import polars as pl
import streamlit as st
from model import Sales_Item
from st_components.st_logger import Log_Level, st_logger

permitted_units = ["lm", "tn", "m3", "m2", "ea", "hr", "sc"]


def cost_item_summary(item: Sales_Item) -> str:
    """Formats a summary line from the item data"""
    unit = item.unit_of_measure
    if item.margin_pct is None:
        margin_pct = 0
    elif item.margin_pct > 0:
        margin_pct = f":green[{item.margin_pct * 100 :.2f}]"
    else:
        margin_pct = f":red[{item.margin_pct * 100 :.2f}]"
    summary_line = (
        f" [ sell: {item.sell_price}/{unit} ]"
        f" [ cost: {item.total_cost_per_unit :.2f}/{unit} ]"
        f" [ margin: {item.margin :.2f}/{unit} ]"
        f" [ **margin_pct : {margin_pct}%** ]"
    )
    return summary_line


def cost_item_buildup(item: Sales_Item) -> Sales_Item | None:
    with st.form(f"{item.code}_cost_buildup"):
        if item.cost_buildup is not None:
            st.write(f"## {item.name}")
            st.write(f"**Summary**: [code: {item.code}]{cost_item_summary(item)}")
            df = item.cost_buildup

            labour_cost_df = df.filter(pl.col("cost_type") == "Labour").drop(
                ["cost_type", "xero_code"]
            )

            supplier_cost_df = df.filter(pl.col("cost_type") == "Supplier").drop(
                ["cost_type", "xero_code"]
            )
            st.write("### Labour Costs")
            e_labour_cost = st.data_editor(
                labour_cost_df.to_pandas(),
                key=f"{item.code}_labour_cost_buildup",
                num_rows="dynamic",
            )

            st.write("### Supplier Costs")
            e_supplier_cost = st.data_editor(
                supplier_cost_df.to_pandas(),
                key=f"{item.code}_supplier_cost_buildup",
                num_rows="dynamic",
            )  # add supplier costu
        submitted = st.form_submit_button("save_changes")
        if submitted:
            e_labour_cost = pl.from_pandas(e_labour_cost).with_columns(  # pyright: ignore [reportPossiblyUnboundVariable]
                pl.lit(item.code).alias("xero_code"),
                pl.lit("Labour").alias("cost_type"),
            )
            e_supplier_cost = pl.from_pandas(e_supplier_cost).with_columns(  # pyright: ignore [reportPossiblyUnboundVariable]
                pl.lit(item.code).alias("xero_code"),
                pl.lit("Supplier").alias("cost_type"),
            )
            cost_builup = pl.concat([e_labour_cost, e_supplier_cost])
            st.write(cost_builup.to_pandas())
            item.cost_buildup = cost_builup
            st_logger(
                Log_Level.INFO, "cost_item_buildup passed back to function caller"
            )
            return item


def cost_items_editor(sales_items: dict[str, Sales_Item]) -> None:
    items = list(sales_items.keys())
    items.insert(0, "See All")
    item_to_edit: str | None = st.selectbox("Select Sales Item To Edit", items)

    if item_to_edit is not None and item_to_edit != "See All":
        saved = cost_item_buildup(sales_items[item_to_edit])  # pyright: ignore[reportArgumentType], already checked in the above conditional
    else:
        for item in sales_items.values():
            with st.expander(f"**{item.code}** - {cost_item_summary(item)}"):
                saved = cost_item_buildup(item)  # pyright: ignore[reportArgumentType], already checked in the above conditional
    return saved
