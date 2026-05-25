# Snowflake Analytics Dashboard with Streamlit

This project provides a Streamlit-based analytics application that integrates with Snowflake, allowing users to execute SQL queries and create interactive dashboards with various visualizations.

## Features

*   **Secure Snowflake Connection:** Connects to Snowflake using credentials from `st.secrets` (for Streamlit Cloud) or environment variables (for local development).
*   **Dynamic Context Selection:** Select Snowflake warehouse, database, schema, and role after a successful connection.
*   **SQL Query Editor:** A text area for users to write and execute custom SQL queries against Snowflake.
*   **Query Results Display:** Shows query results in an interactive Pandas DataFrame.
*   **Query History:** Maintains a history of executed queries, allowing users to re-load past queries.
*   **Dynamic Charting:** Supports various chart types (Bar, Line, Area, Scatter, Pie, Histogram, Metric) generated from query results.
*   **Interactive Dashboard:** Users can add multiple charts to a dashboard, which are then dynamically rendered.
*   **Dashboard Filters:** Apply interactive filters to dashboard charts based on data columns.
*   **Caching:** Leverages `st.cache_data` and `st.cache_resource` for efficient data retrieval and connection management.
*   **Error Handling:** Provides clear feedback for connection and query execution errors.

## Getting Started

### Prerequisites

*   Python 3.8+
*   Access to a Snowflake account.

### Installation

1.  **Clone the repository:**