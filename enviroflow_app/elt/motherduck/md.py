import itertools
import sys
from dataclasses import dataclass
from functools import cached_property

import duckdb
import pandas as pd
import polars as pl
from loguru import logger

from enviroflow_app.helpers.str_helpers import check_sql_entity_names

DDB_LOG_CONF = {
    "handlers": [
        {"sink": sys.stdout},
        {"sink": "logs/duckdb.log", "rotation": "1 day", "retention": "30 days"},
    ],
    "extra": {"user": "andrew"},
}
logger.configure(**DDB_LOG_CONF)


@dataclass(repr=False)
class MotherDuck:
    """Class to interact with the MotherDuck database"""

    token: str
    db_name: str

    @cached_property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Establishes and returns a cached connection to the DuckDB database.

        Returns:
            duckdb.DuckDBPyConnection: The DuckDB connection object.

        """
        con_str = f"md:{self.db_name}?motherduck_token={self.token}"
        logger.info(f"Connecting to {self.db_name} on mother duck ")
        conn = duckdb.connect(con_str)
        conn.execute("SET GLOBAL pandas_analyze_sample=100000")
        logger.info(f"connected to {self.db_name} on mother duck ")
        return conn

    def get_table(self, table_name: str) -> pl.DataFrame:
        """Retrieves a table from the database as a Polars DataFrame.

        Args:
            table_name (str): The name of the table to retrieve.

        Returns:
            pl.DataFrame: The retrieved table as a Polars DataFrame.

        """
        name = check_sql_entity_names(table_name)
        logger.info(f"getting table {table_name} from {self.db_name} on mother duck ")

        # Check if connection is still valid
        try:
            # Test connection with a simple query
            self.conn.execute("SELECT 1").fetchall()
        except duckdb.Error:
            # Reconnect if connection is invalid
            logger.warning("Connection appears to be invalid, reconnecting...")
            self.__dict__.pop("conn", None)  # Clear cached connection
            conn = self.conn  # This will recreate the connection

        df = self.conn.query(f"SELECT * FROM {name}").pl()
        logger.info(f"retrieved table {table_name} from {self.db_name} on mother duck ")
        return df

    def get_table_list(self) -> list[str]:
        """Retrieves a list of all tables in the database.

        Returns:
            list[str]: A list of table names.

        """
        return list(itertools.chain(*self.conn.execute("SHOW TABLES").fetchall()))

    def save_table(self, table_name: str, table: pl.DataFrame):
        """Saves a Polars DataFrame to the database, creating or replacing the table.

        Args:
            table_name (str): The name of the table to save.
            table (pl.DataFrame): The Polars DataFrame to save.

        """
        name = check_sql_entity_names(table_name)
        # check if table is pandas dataframe
        if isinstance(table, pd.DataFrame):
            table_to_save = table
        else:
            table_to_save = table.to_pandas()
        try:
            self.conn.execute(
                f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM table_to_save",
            )
        except duckdb.Error as e:
            logger.error(f"duckdb error:\n {e}\n")
            logger.info(
                f"saving table {table_name} with {table_to_save.columns} columns and shape:{table_to_save.shape} {self.db_name} on mother duck ",
            )
            self.conn.execute(
                f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM table_to_save",
            )

        logger.info(f"saved table {table_name} to {self.db_name} on mother duck ")

    def run_sql(self, sql: str):
        """Executes an SQL query on the database.

        Args:
            sql (str): The SQL query to execute.

        Returns:
            Any: The result of the SQL query execution.

        """
        logger.info(f"running sql:\n {sql}")
        return self.conn.execute(sql)
