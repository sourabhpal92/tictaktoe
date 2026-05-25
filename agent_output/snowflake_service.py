import snowflake.connector
import pandas as pd
import streamlit as st
from constants import DEFAULT_QUERY_LIMIT, DEFAULT_QUERY_TIMEOUT_SECONDS

@st.cache_resource(ttl=3600) # Cache connection object for 1 hour
def get_connection(credentials: dict, context: dict = None) -> snowflake.connector.connection:
    """
    Establishes and returns a cached Snowflake connection object.
    """
    try:
        if not credentials:
            st.error("Snowflake credentials are not provided.")
            return None

        conn_params = {
            'account': credentials['account'],
            'user': credentials['user'],
            'password': credentials['password']
        }

        # Add optional context parameters if provided
        if context:
            if context.get('role'):
                conn_params['role'] = context['role']
            if context.get('warehouse'):
                conn_params['warehouse'] = context['warehouse']
            if context.get('database'):
                conn_params['database'] = context['database']
            if context.get('schema'):
                conn_params['schema'] = context['schema']
        
        st.info("Attempting to connect to Snowflake...")
        conn = snowflake.connector.connect(**conn_params)
        
        # Test the connection by executing a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT CURRENT_VERSION()")
            st.success(f"Successfully connected to Snowflake (Version: {cursor.fetchone()[0]})")
        
        return conn

    except snowflake.connector.errors.ProgrammingError as e:
        st.error(f"Snowflake Connection Error: {e.msg}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during connection: {e}")
        return None

@st.cache_data(ttl=600, show_spinner="Executing query and fetching data...") # Cache query results for 10 minutes
def execute_query(connection: snowflake.connector.connection, query: str,
                  row_limit: int = DEFAULT_QUERY_LIMIT,
                  timeout: int = DEFAULT_QUERY_TIMEOUT_SECONDS) -> pd.DataFrame:
    """
    Executes a SQL query against Snowflake and returns results as a Pandas DataFrame.
    Includes row limit and timeout.
    """
    if not connection:
        st.error("No active Snowflake connection.")
        return pd.DataFrame()

    try:
        with connection.cursor() as cursor:
            # Set query timeout for the current session
            cursor.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {timeout};")

            # Execute the actual query
            cursor.execute(query)

            # Fetch results and convert to DataFrame
            df = cursor.fetch_pandas_all()
            
            # Apply row limit after fetching, if needed (Snowflake has LIMIT clause but this adds safety)
            if row_limit and len(df) > row_limit:
                df = df.head(row_limit)
                st.warning(f"Query results truncated to {row_limit} rows.")
            
            st.success(f"Query executed successfully. Fetched {len(df)} rows.")
            return df
            
    except snowflake.connector.errors.ProgrammingError as e:
        st.error(f"Snowflake Query Error: {e.msg}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred during query execution: {e}")
        return pd.DataFrame()

def _fetch_metadata(connection: snowflake.connector.connection, query: str) -> list[str]:
    """Helper to fetch a list of names (e.g., warehouses, databases)."""
    if not connection:
        return []
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]
    except Exception:
        return [] # Return empty list on error for metadata functions

@st.cache_data(ttl=3600)
def get_warehouses(connection: snowflake.connector.connection) -> list[str]:
    """Retrieves available warehouses."""
    return _fetch_metadata(connection, "SHOW WAREHOUSES;")

@st.cache_data(ttl=3600)
def get_databases(connection: snowflake.connector.connection) -> list[str]:
    """Retrieves available databases."""
    return _fetch_metadata(connection, "SHOW DATABASES;")

@st.cache_data(ttl=3600)
def get_schemas(connection: snowflake.connector.connection, database: str) -> list[str]:
    """Retrieves available schemas for a given database."""
    if not database:
        return []
    return _fetch_metadata(connection, f"SHOW SCHEMAS IN DATABASE {database};")

@st.cache_data(ttl=3600)
def get_roles(connection: snowflake.connector.connection) -> list[str]:
    """Retrieves available roles."""
    return _fetch_metadata(connection, "SHOW ROLES;")