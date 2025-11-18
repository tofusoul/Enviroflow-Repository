import os

from helpers.str_helpers import check_sql_entity_names
from jinja2 import Template


def filter_table_by_column_value(
    table_name: str,
    column_name: str,
    ilike_matches: list[str],
    ilike_exceptions: list[str],
) -> str:
    """Filters quotes by matching cells in a column to any of the ilike strings in the match list, and removes any rows where the column matches the exceptions list of strings"""
    table_name = check_sql_entity_names(table_name)
    column_name = check_sql_entity_names(column_name)
    matches = []
    for string in ilike_matches:
        matches.append(f"%{string}%")
    exceptions = []
    for string in ilike_exceptions:
        exceptions.append(f"%{string}%")

    print(os.getcwd())
    with open("enviroflow_app/db_queries/filter_table.sql") as sql:
        sql_template = sql.read()
    query_str = Template(sql_template).render(
        table_name=table_name,
        column_name=column_name,
        ilike_matches=matches,
        ilike_exceptions=exceptions,
    )
    return query_str
