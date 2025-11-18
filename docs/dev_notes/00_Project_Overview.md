# Project Overview

Enviroflow App is a Streamlit-based business intelligence application built for a drainage and construction company. Its core function is to implement a robust ELT (Extract-Load-Transform) pipeline, integrating data from disparate sources like Trello, Xero, Float, and Google Sheets into a centralized MotherDuck (cloud DuckDB) instance for comprehensive project performance analysis.

The project features an automated data synchronization process using GitHub Actions, which ensures that data from key sources is fetched and updated on an hourly basis.

## Purpose

The primary goals of the application are to:
1.  **Centralize Data**: Aggregate data from various business systems into a single source of truth.
2.  **Enable Business Intelligence**: Provide powerful job costing analysis and financial insights.
3.  **Support Decision-Making**: Equip the team with up-to-date information for better planning.
4.  **Automate Processes**: Streamline routine tasks such as generating subcontractor agreements.

## Technology Stack

The application is built with a modern, Python-centric technology stack:

-   **Frontend**: [Streamlit](https://streamlit.io/) for creating interactive web interfaces.
-   **Database**: [MotherDuck](https://motherduck.com/) for cloud-hosted DuckDB storage and analytics.
-   **Data Processing**:
    -   [Polars](https://pola.rs/) for high-performance DataFrame manipulation.
    -   [Pandas](https://pandas.pydata.org/) for data analysis and compatibility.
-   **CLI**: [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/en/latest/) for a modern, user-friendly command-line interface.
-   **Development**: [Poetry](https://python-poetry.org/) for dependency management.
-   **CI/CD**: [GitHub Actions](https://github.com/features/actions) for automated data synchronization.

## External Integrations

The pipeline extracts data from several key business systems:

-   **Trello**: Project management, job tracking, and workflow status.
-   **Xero**: Financial data, invoices, and supplier costs (currently via manual report uploads).
-   **Float**: Resource scheduling and labor allocation.
-   **Google Sheets**: Legacy data and supplementary manual data entry.
-   **Simpro**: Service management software data.
