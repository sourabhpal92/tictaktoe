import streamlit as st
import pandas as pd
import uuid # For unique chart IDs

from config import get_snowflake_credentials
from snowflake_service import (
    get_connection, execute_query,
    get_warehouses, get_databases, get_schemas, get_roles
)
from viz_builder import build_chart
from security_utils import validate_sql_query
from constants import DEFAULT_QUERY_LIMIT, DEFAULT_QUERY_TIMEOUT_SECONDS, SUPPORTED_CHART_TYPES

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Snowflake Analytics Dashboard")

# --- Initialize Session State ---
if 'sf_connection' not in st.session_state:
    st.session_state.sf_connection = None
if 'current_query' not in st.session_state:
    st.session_state.current_query = "SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER LIMIT 100;"
if 'query_results_df' not in st.session_state:
    st.session_state.query_results_df = pd.DataFrame()
if 'active_dashboard' not in st.session_state:
    st.session_state.active_dashboard = []
if 'sf_context' not in st.session_state:
    st.session_state.sf_context = {}
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'query_settings' not in st.session_state:
    st.session_state.query_settings = {
        'row_limit': DEFAULT_QUERY_LIMIT,
        'timeout': DEFAULT_QUERY_TIMEOUT_SECONDS
    }
if 'connection_params' not in st.session_state:
    st.session_state.connection_params = get_snowflake_credentials() or {}

# --- Helper Functions ---
def clear_dashboard():
    """Clears all charts from the active dashboard."""
    st.session_state.active_dashboard = []
    st.session_state.query_results_df = pd.DataFrame() # Also clear results to reset context

def connect_to_snowflake_handler():
    """Handles the connection button click."""
    st.session_state.sf_connection = get_connection(
        st.session_state.connection_params,
        st.session_state.sf_context
    )

def execute_query_handler():
    """Handles query execution."""
    if not st.session_state.sf_connection:
        st.error("Please connect to Snowflake first.")
        return

    is_valid, message = validate_sql_query(st.session_state.current_query)
    if not is_valid:
        st.error(f"SQL Validation Error: {message}")
        return

    # Invalidate @st.cache_data for execute_query before calling it
    # This ensures new query text gets new data
    st.cache_data.clear() 

    df = execute_query(
        st.session_state.sf_connection,
        st.session_state.current_query,
        row_limit=st.session_state.query_settings['row_limit'],
        timeout=st.session_state.query_settings['timeout']
    )
    st.session_state.query_results_df = df
    if st.session_state.current_query not in st.session_state.query_history:
        st.session_state.query_history.insert(0, st.session_state.current_query)
        if len(st.session_state.query_history) > 10: # Keep last 10 queries
            st.session_state.query_history.pop()

def add_chart_to_dashboard(chart_type, x_col, y_col, names_col, values_col, color_col, size_col, value_col, delta_col, title):
    """Adds a new chart configuration to the dashboard."""
    chart_config = {
        'id': str(uuid.uuid4()), # Unique ID for each chart
        'type': chart_type,
        'title': title
    }
    # Add relevant columns based on chart type
    if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot", "Area Chart"]:
        chart_config['x_col'] = x_col
        chart_config['y_col'] = y_col
        chart_config['color_col'] = color_col
        if chart_type == "Scatter Plot":
            chart_config['size_col'] = size_col
    elif chart_type == "Pie Chart":
        chart_config['names_col'] = names_col
        chart_config['values_col'] = values_col
    elif chart_type == "Histogram":
        chart_config['x_col'] = x_col
        chart_config['color_col'] = color_col
    elif chart_type == "KPI Metric":
        chart_config['value_col'] = value_col
        chart_config['delta_col'] = delta_col

    st.session_state.active_dashboard.append(chart_config)


# --- UI Layout ---

st.sidebar.title("Snowflake Analytics App")

# --- Sidebar: Connection Configuration ---
with st.sidebar.expander("❄️ Snowflake Connection", expanded=not st.session_state.sf_connection):
    st.session_state.connection_params['account'] = st.text_input(
        "Account", value=st.session_state.connection_params.get('account', ''), key="account_input"
    )
    st.session_state.connection_params['user'] = st.text_input(
        "User", value=st.session_state.connection_params.get('user', ''), key="user_input"
    )
    st.session_state.connection_params['password'] = st.text_input(
        "Password", type="password", value=st.session_state.connection_params.get('password', ''), key="password_input"
    )

    if st.button("Connect to Snowflake", use_container_width=True):
        connect_to_snowflake_handler()

    if st.session_state.sf_connection:
        st.success("Connected to Snowflake!")
        # Fetch available context items
        warehouses = get_warehouses(st.session_state.sf_connection)
        databases = get_databases(st.session_state.sf_connection)
        roles = get_roles(st.session_state.sf_connection)
        
        # Determine current selection or default
        current_warehouse = st.session_state.sf_context.get('warehouse')
        current_database = st.session_state.sf_context.get('database')
        current_role = st.session_state.sf_context.get('role')

        # Selectboxes for context
        selected_warehouse = st.selectbox(
            "Warehouse", options=warehouses, 
            index=warehouses.index(current_warehouse) if current_warehouse in warehouses else 0,
            key="sf_warehouse"
        )
        selected_database = st.selectbox(
            "Database", options=databases, 
            index=databases.index(current_database) if current_database in databases else 0,
            key="sf_database"
        )
        # Update schemas when database changes
        schemas = get_schemas(st.session_state.sf_connection, selected_database)
        current_schema = st.session_state.sf_context.get('schema')
        selected_schema = st.selectbox(
            "Schema", options=schemas, 
            index=schemas.index(current_schema) if current_schema in schemas else 0,
            key="sf_schema"
        )
        selected_role = st.selectbox(
            "Role", options=roles, 
            index=roles.index(current_role) if current_role in roles else 0,
            key="sf_role"
        )

        # Update session state context
        st.session_state.sf_context = {
            'warehouse': selected_warehouse,
            'database': selected_database,
            'schema': selected_schema,
            'role': selected_role
        }
        st.info(f"Context: WH={selected_warehouse}, DB={selected_database}, Schema={selected_schema}, Role={selected_role}")
    else:
        st.warning("Not connected to Snowflake.")

# --- Sidebar: Query Settings ---
with st.sidebar.expander("⚙️ Query Settings"):
    st.session_state.query_settings['row_limit'] = st.number_input(
        "Row Limit", min_value=1, value=st.session_state.query_settings['row_limit'], step=100
    )
    st.session_state.query_settings['timeout'] = st.number_input(
        "Query Timeout (seconds)", min_value=30, value=st.session_state.query_settings['timeout'], step=30
    )

# --- Main Content Area ---
st.header("SQL Query Editor")

sql_query_input = st.text_area(
    "Enter your SQL query here:",
    height=200,
    value=st.session_state.current_query,
    key="sql_editor"
)
st.session_state.current_query = sql_query_input

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Execute Query", type="primary", use_container_width=True):
        execute_query_handler()
with col2:
    if st.session_state.query_results_df.empty and not st.session_state.active_dashboard:
        st.button("Clear Dashboard", use_container_width=True, disabled=True)
    else:
        if st.button("Clear Dashboard", use_container_width=True, help="Clear all charts and query results"):
            clear_dashboard()


st.subheader("Query Results")
if not st.session_state.query_results_df.empty:
    st.dataframe(st.session_state.query_results_df, use_container_width=True, height=300)
    csv = st.session_state.query_results_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Export Results to CSV",
        data=csv,
        file_name="query_results.csv",
        mime="text/csv",
    )
else:
    st.info("Execute a query to see results here.")

st.subheader("Query History")
if st.session_state.query_history:
    selected_query_from_history = st.selectbox(
        "Select a past query to re-run or edit:",
        options=[""] + st.session_state.query_history,
        index=0,
        key="query_history_select"
    )
    if selected_query_from_history:
        st.session_state.current_query = selected_query_from_history
        st.rerun() # Rerun to update the text_area

# --- Dashboard Builder ---
st.header("Dashboard Builder")

if not st.session_state.query_results_df.empty:
    df_columns = st.session_state.query_results_df.columns.tolist()
    
    with st.expander("➕ Add New Chart", expanded=True):
        chart_type = st.selectbox("Select Chart Type", SUPPORTED_CHART_TYPES, key="chart_type_select")
        chart_title = st.text_input("Chart Title", value=f"{chart_type} (Query Results)", key="chart_title_input")

        # Dynamic column selectors based on chart type
        x_col, y_col, names_col, values_col, color_col, size_col, value_col, delta_col = [None] * 8

        if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot", "Area Chart", "Histogram"]:
            x_col = st.selectbox("X-axis Column", options=[""] + df_columns, key="x_col_select")
            if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot", "Area Chart"]:
                y_col = st.selectbox("Y-axis Column", options=[""] + df_columns, key="y_col_select")
            if chart_type in ["Bar Chart", "Line Chart", "Scatter Plot", "Area Chart", "Histogram"]:
                color_col = st.selectbox("Color By (Optional)", options=[""] + df_columns, key="color_col_select")
            if chart_type == "Scatter Plot":
                size_col = st.selectbox("Size By (Optional)", options=[""] + df_columns, key="size_col_select")
        elif chart_type == "Pie Chart":
            names_col = st.selectbox("Names Column", options=[""] + df_columns, key="names_col_select")
            values_col = st.selectbox("Values Column", options=[""] + df_columns, key="values_col_select")
        elif chart_type == "KPI Metric":
            value_col = st.selectbox("Value Column", options=[""] + df_columns, help="Select a numeric column for the main KPI value. Takes the first row's value.", key="value_col_select")
            delta_col = st.selectbox("Delta Column (Optional)", options=[""] + df_columns, help="Select a numeric column representing the change. Takes the first row's value.", key="delta_col_select")

        if st.button("Add Chart to Dashboard", use_container_width=True, key="add_chart_button"):
            add_chart_to_dashboard(chart_type, x_col, y_col, names_col, values_col, color_col, size_col, value_col, delta_col, chart_title)
            st.rerun() # Rerun to display the new chart

    st.markdown("---") # Separator

    # --- Display Dashboard ---
    st.subheader("Your Interactive Dashboard")
    if st.session_state.active_dashboard:
        # Simple two-column layout for charts
        num_charts = len(st.session_state.active_dashboard)
        cols = st.columns(2) # Two columns per row
        
        for i, chart_config in enumerate(st.session_state.active_dashboard):
            with cols[i % 2]: # Place chart in appropriate column
                st.write(f"### {chart_config.get('title', 'Untitled Chart')}")
                try:
                    fig = build_chart(st.session_state.query_results_df, chart_config)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error rendering chart '{chart_config.get('title')}': {e}")
                
                if st.button(f"Remove Chart '{chart_config.get('title', 'Untitled')}'", key=f"remove_chart_{chart_config['id']}", use_container_width=True):
                    st.session_state.active_dashboard.pop(i)
                    st.rerun()
                st.markdown("---")
    else:
        st.info("Add charts above to build your dashboard.")
else:
    st.warning("Execute a SQL query first to populate data for dashboarding.")