# Database Operations Contract (Updated for Streamlit Data Management Interface)# Database Operations Contract



## Connection Management## Connection Management



```python```python

class MotherDuckConnection:@dataclass

    """Connection to MotherDuck database for business data operations."""class MotherDuckConnection:

    def get_table_list(self) -> list[str]:    """Contract for MotherDuck database connection operations."""

        """Return list of available business tables."""

        pass

    def get_table(self, table_name: str) -> pl.DataFrame:    # Database Operations Contract (Updated for Streamlit Data Management Interface)

        """Fetch all data from a specified table as Polars DataFrame."""

        pass    ## Connection Management

    def run_sql(self, sql: str) -> pl.DataFrame:

        """Execute SQL query and return results as Polars DataFrame."""    ```python

        pass    class MotherDuckConnection:

```        """Connection to MotherDuck database for business data operations."""

        def get_table_list(self) -> list[str]:

## Query Helper Functions            """Return list of available business tables."""

            pass

```python        def get_table(self, table_name: str) -> pl.DataFrame:

def load_predefined_queries() -> List[Dict[str, Any]]:            """Fetch all data from a specified table as Polars DataFrame."""

    """            pass

    Load all predefined SQL and Jinja2 template queries from the db_queries directory.        def run_sql(self, sql: str) -> pl.DataFrame:

    Returns a list of query definitions with name, SQL, template status, and variables.            """Execute SQL query and return results as Polars DataFrame."""

    """            pass

    pass    ```



def execute_query_with_template(md: MotherDuckConnection, query: str, template_vars: Optional[Dict[str, Any]] = None) -> pl.DataFrame:    ## Query Helper Functions

    """

    Execute a SQL query, rendering Jinja2 templates if needed, and return results as Polars DataFrame.    ```python

    """    def load_predefined_queries() -> List[Dict[str, Any]]:

    pass        """

```        Load all predefined SQL and Jinja2 template queries from the db_queries directory.

        Returns a list of query definitions with name, SQL, template status, and variables.

## Template Processing        """

        pass

```python

def extract_template_variables(template: str) -> List[str]:    def execute_query_with_template(md: MotherDuckConnection, query: str, template_vars: Optional[Dict[str, Any]] = None) -> pl.DataFrame:

    """        """

    Extract Jinja2 variable names from SQL template using regex.        Execute a SQL query, rendering Jinja2 templates if needed, and return results as Polars DataFrame.

    """        """

    pass        pass

```    ```



## Error Handling    ## Template Processing



```python    ```python

class DataExplorerError(Exception):    def extract_template_variables(template: str) -> List[str]:

    """Base exception for Data Explorer operations."""        """

    pass        Extract Jinja2 variable names from SQL template using regex.

```        """

        pass

## Data Type Definitions    ```



```python    ## Error Handling

from typing import Dict, List, Any, Optional

import polars as pl    ```python

    class DataExplorerError(Exception):

# Query definition structure        """Base exception for Data Explorer operations."""

QueryDefinition = Dict[str, Any]  # {"name": str, "sql": str, "is_template": bool, "variables": List[str], "type": str}        pass

```    ```



These contracts define the expected behavior and interfaces for all business data operations, query processing, and error handling in the Streamlit Data Management Interface.    ## Data Type Definitions

    ```python
    from typing import Dict, List, Any, Optional
    import polars as pl

    # Query definition structure
    QueryDefinition = Dict[str, Any]  # {"name": str, "sql": str, "is_template": bool, "variables": List[str], "type": str}
    ```

    These contracts define the expected behavior and interfaces for all business data operations, query processing, and error handling in the Streamlit Data Management Interface.
