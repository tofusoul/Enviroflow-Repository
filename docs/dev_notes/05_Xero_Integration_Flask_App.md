# Xero Integration Flask App

This document provides an overview of the standalone Flask application located in the `/xero` directory, which is used for handling Xero API integration.

## Purpose

The Xero Flask app is a utility built to manage the OAuth 2.0 authentication process required by the Xero API. Its primary purpose is to perform a one-time, comprehensive extraction of all quotes from a connected Xero organization.

This application is **not** part of the main Streamlit application or the automated data pipeline. It is a separate tool for manual data fetching.

## Key Functionality

-   **OAuth 2.0 Authentication**: Handles the complete, user-driven OAuth 2.0 flow to authorize access to a Xero account.
-   **Token Management**: Manages and persists the Xero API token using a Flask session.
-   **Data Extraction**: Provides a web endpoint (`/all_quotes`) to fetch all quotes from the Xero Accounting API, handling pagination automatically.
-   **Data Persistence**: After fetching, the application saves the quotes data in multiple locations and formats:
    -   **Local Parquet Files**:
        -   `Data/xero_data/quotes_df.parquet`
        -   `Data/xero_data/quotes_df_human.parquet`
    -   **Local CSV Files**:
        -   `Data/xero_data/quotes_df.csv`
        -   `Data/xero_data/quotes_df_human.csv`
    -   **MotherDuck**: Uploads the complete, raw dataset to the `full_xero_quotes` table in the `enviroflow` MotherDuck database.

## How to Use

### 1. Configuration

-   Create a `config.py` file inside the `xero/` directory.
-   Add your Xero App credentials to this file:
    ```python
    CLIENT_ID = "YOUR_XERO_CLIENT_ID"
    CLIENT_SECRET = "YOUR_XERO_CLIENT_SECRET"
    ```

### 2. Running the App

1.  **Navigate to the `xero` directory.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Flask application:**
    ```bash
    python app.py
    ```
4.  **Authenticate with Xero:**
    -   Open your browser and go to `http://localhost:5000/login`.
    -   This will redirect you to the Xero login page. Log in and authorize the application to access your organization's data.
    -   You will be redirected back to the application upon success.

5.  **Fetch Quotes:**
    -   Navigate to `http://localhost:5000/all_quotes`.
    -   Click the **"Fetch JSON"** button.
    -   The application will then fetch all quotes, process them, and save them to the locations listed above.

## Architectural Note

This Flask application serves as a critical but separate part of the data ecosystem. The long-term strategy should be to deprecate this manual tool and integrate its data extraction capabilities directly into the new, modular CLI pipeline (`enviroflow_app/cli/`). This would allow for automated, unattended fetching of Xero data.
