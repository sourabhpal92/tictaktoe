# Streamlit Snowflake Analytics App

This project is a Streamlit-based analytics application designed for interactive data analysis and dashboarding, powered by Snowflake Data Cloud. It enables users to connect to Snowflake, execute ad-hoc SQL queries, dynamically visualize results, and build interactive dashboards.

## Features

*   **Secure Snowflake Connection:** Connects to Snowflake using credentials from `st.secrets` (production) or `.env` (local development).
*   **Context Management:** Allows selecting Snowflake warehouse, database, schema, and role.
*   **SQL Query Editor:** Execute custom SQL queries and view results as a Pandas DataFrame.
*   **Basic SQL Validation:** Prevents multi-statement execution and checks for common malicious keywords.
*   **Dynamic Visualization:** Supports various chart types (Bar, Line, Pie, Scatter, Area, Histogram, KPI) using Plotly.
*   **Interactive Dashboarding:** Build multi-chart dashboards with dynamic filtering capabilities.
*   **Session State Management:** Maintains connection, query results, and dashboard configurations throughout the user session.
*   **Performance Optimization:** Utilizes Streamlit's caching mechanisms for Snowflake connection and query results.
*   **Data Export:** Export query results to CSV.

## Project Structure

*   `app.py`: The main Streamlit application entry point, orchestrating UI, session state, and interaction flow.
*   `config.py`: Handles configuration loading, primarily for Snowflake credentials from `st.secrets` or `.env`.
*   `snowflake_service.py`: Encapsulates all interactions with Snowflake, including connection, query execution, and metadata retrieval.
*   `viz_builder.py`: Module responsible for generating various Plotly chart types from Pandas DataFrames.
*   `security_utils.py`: Provides basic SQL query validation to enhance security.
*   `constants.py`: Defines application-wide constants like default query limits and supported chart types.
*   `requirements.txt`: Lists all Python dependencies.
*   `.env`: Example file for local environment variables (credentials should be handled securely in production).

## Setup and Local Development

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### 1. Clone the repository