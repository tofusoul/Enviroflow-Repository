import polars as pl
import streamlit as st

from enviroflow_app.elt.motherduck import md

ACCEPTED_FILE_TYPES = [
    "parquet",
    "csv",
    "xlsx",
    "xls",
    "xlsb",
    "xlsm",
    "xls",
]

UPDATABLE_TABLES = ["xero_costs"]


def upload_xero_reports(conn: md.MotherDuck) -> None:
    st.caption(
        "This tool allows you to upload xero reports, currently, there is only the cost report supported",
    )
    read_csv_options = {"skip_rows": 4, "infer_schema_length": 10000}
    table_to_update = st.selectbox("update table", UPDATABLE_TABLES)
    ow = st.toggle("over write table", value=True)
    uploaded_file = st.file_uploader("Upload a file", type=ACCEPTED_FILE_TYPES)
    if not ow:
        st.warning("appending to cost report not supported yet")
    st.dataframe(uploaded_file)
    if uploaded_file is None:
        st.info("Please upload a file of type: " + ", ".join(ACCEPTED_FILE_TYPES))
        st.stop()
    else:
        match (table_to_update, uploaded_file.type):
            case (
                "xero_costs",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ):
                table: pl.DataFrame = pl.read_excel(
                    uploaded_file,
                    read_options=read_csv_options,
                )
                table = table.with_columns(
                    pl.col("Date")
                    .str.strptime(
                        pl.Date,
                        format="%d %b %Y",
                        strict=False,
                    )
                    .cast(pl.Datetime)
                    .dt.cast_time_unit(
                        "ns",
                    ),  # casting time unit so it can match fetched table from db
                ).drop_nulls()

                st.toast(f"👁️ read and loaded:\n `{uploaded_file.name}`")
                conn.save_table(table_to_update, table)
                st.toast(f"👁️ updated table: `{table_to_update}`")

            case (
                _,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ):
                if table_to_update not in UPDATABLE_TABLES:
                    st.error("🚧 write a handler Andrew")

            case _:
                st.error("🚧 write a handler Andrew")
