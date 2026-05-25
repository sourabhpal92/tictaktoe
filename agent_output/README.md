# Snowflake Analytics Dashboard

This project is a Streamlit-based analytics application that integrates with Snowflake, allowing users to execute SQL queries, view tabular results, and create interactive dashboards with various visualizations.

## Features

*   **Secure Snowflake Connection:** Connect to Snowflake using credentials from `st.secrets` (Streamlit Cloud) or `.env` file (local).
*   **Dynamic Context Switching:** Easily switch between Snowflake warehouses, databases, schemas, and roles.
*   **SQL Query Editor:** Write and execute custom SQL queries directly from the application.
*   **Query History & Caching:** View past queries and benefit from cached results for frequently run queries.
*   **Interactive Data Display:** View query results in a `st.dataframe` and export them as CSV.
*   **Dynamic Chart Generation:** Create various chart types (Bar, Line, Area, Scatter, Pie) and KPI metrics from query results using Altair.
*   **Dashboard Layout:** Arrange multiple charts on a dashboard.
*   **Global Filtering:** Apply interactive filters to the entire dashboard based on columns from the query results.
*   **Error Handling:** Graceful display of connection and SQL execution errors.

## Technologies Used

*   **Streamlit:** For building the interactive web application UI.
*   **Snowflake:** The cloud data warehouse.
*   **`snowflake-connector-python`:** Python connector for Snowflake.
*   **`pandas`:** For data manipulation and processing.
*   **`altair`:** For declarative and interactive data visualizations.
*   **`python-dotenv`:** For managing environment variables locally.

## Setup and Local Development

### Prerequisites

*   Python 3.8+
*   Git (optional, for cloning the repository)
*   A Snowflake account with necessary credentials.

### Steps

1.  **Clone the repository (if applicable):**