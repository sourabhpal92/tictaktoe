import streamlit as st
import pandas as pd
import altair as alt
import os
from dotenv import load_dotenv

# Local imports
from src.snowflake_dal import SnowflakeConnector
from src.chart_generator import generate_chart, generate_kpi_metric

# Load environment variables for local development
load_dotenv()

# Initialize Snowflake Connector
sf_connector = SnowflakeConnector()

# --- Utility Functions ---
@st.cache_resource
def get_snowflake_connector():
    """Returns a cached SnowflakeConnector instance."""
    return SnowflakeConnector()

def get_snowflake_credentials():
    """
    Loads Snowflake credentials from st.secrets or environment variables.
    """
    # Prefer st.secrets for Streamlit Cloud deployment
    if "snowflake" in st.secrets:
        return st.secrets["snowflake"]
    
    # Fallback to environment variables for local development
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }

def initialize_session_state():
    """Initializes all necessary session state variables."""
    if "connected_to_snowflake" not in st.session_state:
        st.session_state.connected_to_snowflake = False
    if "snowflake_connection_params" not in st.session_state:
        st.session_state.snowflake_connection_params = {}
    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "latest_dataframe" not in st.session_state:
        st.session_state.latest_dataframe = pd.DataFrame()
    if "dashboard_charts" not in st.session_state:
        st.session_state.dashboard_charts = []
    if "active_filters" not in st.session_state:
        st.session_state.active_filters = {}
    if "available_metadata" not in st.session_state:
        st.session_state.available_metadata = {"warehouses": [], "databases": [], "schemas": [], "roles": []}
    if "latest_query_text" not in st.session_state:
        st.session_state.latest_query_text = ""
    if "latest_query_error" not in st.session_state:
        st.session_state.latest_query_error = None
    if "chart_config_key" not in st.session_state:
        st.session_state.chart_config_key = 0 # Used to reset chart config UI elements

def connect_to_snowflake(account, user, password, warehouse, database, schema, role):
    """Attempts to connect to Snowflake and updates session state."""
    try:
        sf_connector = get_snowflake_connector()
        with st.spinner("Connecting to Snowflake..."):
            sf_connector.connect(account, user, password, warehouse, database, schema, role)
        
        st.session_state.connected_to_snowflake = True
        st.session_state.snowflake_connection_params = {
            "account": account, "user": user, "warehouse": warehouse,
            "database": database, "schema": schema, "role": role
        }
        
        # Fetch metadata for dropdowns
        st.session_state.available_metadata["warehouses"] = sf_connector.get_metadata("warehouses")
        st.session_state.available_metadata["databases"] = sf_connector.get_metadata("databases")
        st.session_state.available_metadata["schemas"] = sf_connector.get_metadata("schemas")
        st.session_state.available_metadata["roles"] = sf_connector.get_metadata("roles")

        st.success("Successfully connected to Snowflake!")
        st.rerun() # Rerun to update UI with connection status and populated dropdowns
    except ConnectionError as e:
        st.session_state.connected_to_snowflake = False
        st.session_state.latest_query_error = str(e)
        st.error(f"Connection Error: {e}")
    except Exception as e:
        st.session_state.connected_to_snowflake = False
        st.session_state.latest_query_error = str(e)
        st.error(f"An unexpected error occurred: {e}")

def disconnect_from_snowflake():
    """Disconnects from Snowflake and resets session state."""
    sf_connector = get_snowflake_connector()
    sf_connector.disconnect()
    st.session_state.connected_to_snowflake = False
    st.session_state.snowflake_connection_params = {}
    st.session_state.query_history = []
    st.session_state.latest_dataframe = pd.DataFrame()
    st.session_state.dashboard_charts = []
    st.session_state.active_filters = {}
    st.session_state.available_metadata = {"warehouses": [], "databases": [], "schemas": [], "roles": []}
    st.session_state.latest_query_text = ""
    st.session_state.latest_query_error = None
    st.success("Disconnected from Snowflake.")
    st.rerun() # Rerun to update UI with disconnected state

@st.cache_data(ttl=3600) # Cache query results for 1 hour
def execute_snowflake_query(query: str, connection_params: dict):
    """
    Executes a Snowflake query and returns a DataFrame.
    This function is wrapped in st.cache_data.
    """
    sf_connector_cached = get_snowflake_connector()
    # Re-establish connection for cached function if not connected, using provided params
    # This is important for cache invalidation based on connection params
    if not sf_connector_cached.is_connected() or sf_connector_cached.connection_params != connection_params:
        sf_connector_cached.connect(
            connection_params["account"], connection_params["user"],
            os.getenv("SNOWFLAKE_PASSWORD") if not st.secrets.get("snowflake") else st.secrets["snowflake"]["password"],
            connection_params.get("warehouse"), connection_params.get("database"),
            connection_params.get("schema"), connection_params.get("role")
        )
    
    df = sf_connector_cached.execute_query(query)
    return df

def apply_filters_to_dataframe(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Applies filters from session state to a DataFrame."""
    filtered_df = df.copy()
    if not filters:
        return filtered_df

    for col, values in filters.items():
        if col in filtered_df.columns and values:
            if pd.api.types.is_numeric_dtype(filtered_df[col]):
                min_val, max_val = values
                filtered_df = filtered_df[(filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)]
            else:
                filtered_df = filtered_df[filtered_df[col].isin(values)]
    return filtered_df


# --- Streamlit UI Layout ---
st.set_page_config(layout="wide", page_title="Snowflake Analytics App")
st.title("❄️ Snowflake Analytics Dashboard")

initialize_session_state()

# --- Sidebar for Connection and Filters ---
with st.sidebar:
    st.header("Snowflake Connection")
    creds = get_snowflake_credentials()

    # Input fields for connection
    st.text_input("Account", value=creds.get("account", ""), key="sf_account",
                  disabled=st.session_state.connected_to_snowflake)
    st.text_input("User", value=creds.get("user", ""), key="sf_user",
                  disabled=st.session_state.connected_to_snowflake)
    st.text_input("Password", type="password", value=creds.get("password", ""), key="sf_password",
                  disabled=st.session_state.connected_to_snowflake)

    # Context selectors
    current_warehouse = st.session_state.snowflake_connection_params.get("warehouse", creds.get("warehouse"))
    current_database = st.session_state.snowflake_connection_params.get("database", creds.get("database"))
    current_schema = st.session_state.snowflake_connection_params.get("schema", creds.get("schema"))
    current_role = st.session_state.snowflake_connection_params.get("role", creds.get("role"))

    # Populate dropdowns only if connected and metadata is available
    if st.session_state.connected_to_snowflake:
        warehouses = st.session_state.available_metadata["warehouses"]
        databases = st.session_state.available_metadata["databases"]
        schemas = st.session_state.available_metadata["schemas"]
        roles = st.session_state.available_metadata["roles"]

        selected_warehouse = st.selectbox("Warehouse", options=warehouses, index=warehouses.index(current_warehouse) if current_warehouse in warehouses else 0, key="sf_warehouse")
        selected_database = st.selectbox("Database", options=databases, index=databases.index(current_database) if current_database in databases else 0, key="sf_database")
        selected_schema = st.selectbox("Schema", options=schemas, index=schemas.index(current_schema) if current_schema in schemas else 0, key="sf_schema")
        selected_role = st.selectbox("Role", options=roles, index=roles.index(current_role) if current_role in roles else 0, key="sf_role")

        # Update context if selections change
        if (selected_warehouse != current_warehouse or
            selected_database != current_database or
            selected_schema != current_schema or
            selected_role != current_role):
            try:
                with st.spinner("Updating Snowflake context..."):
                    sf_connector = get_snowflake_connector()
                    sf_connector.set_context(selected_warehouse, selected_database, selected_schema, selected_role)
                    st.session_state.snowflake_connection_params["warehouse"] = selected_warehouse
                    st.session_state.snowflake_connection_params["database"] = selected_database
                    st.session_state.snowflake_connection_params["schema"] = selected_schema
                    st.session_state.snowflake_connection_params["role"] = selected_role
                st.success("Snowflake context updated.")
                # After updating context, refresh schemas if database changed
                if selected_database != current_database:
                     st.session_state.available_metadata["schemas"] = sf_connector.get_metadata("schemas")
            except Exception as e:
                st.error(f"Failed to update context: {e}")

    col1_conn, col2_conn = st.columns(2)
    with col1_conn:
        if st.button("Connect", disabled=st.session_state.connected_to_snowflake, use_container_width=True):
            if st.session_state.sf_account and st.session_state.sf_user and st.session_state.sf_password:
                connect_to_snowflake(
                    st.session_state.sf_account,
                    st.session_state.sf_user,
                    st.session_state.sf_password,
                    st.session_state.sf_warehouse if st.session_state.connected_to_snowflake else creds.get("warehouse"),
                    st.session_state.sf_database if st.session_state.connected_to_snowflake else creds.get("database"),
                    st.session_state.sf_schema if st.session_state.connected_to_snowflake else creds.get("schema"),
                    st.session_state.sf_role if st.session_state.connected_to_snowflake else creds.get("role")
                )
            else:
                st.warning("Please enter all required Snowflake credentials.")
    with col2_conn:
        if st.button("Disconnect", disabled=not st.session_state.connected_to_snowflake, use_container_width=True):
            disconnect_from_snowflake()

    if st.session_state.connected_to_snowflake:
        st.success(f"Connected to: {st.session_state.snowflake_connection_params.get('account')}")
        st.markdown(f"**Warehouse:** {st.session_state.snowflake_connection_params.get('warehouse')}  \n**Database:** {st.session_state.snowflake_connection_params.get('database')}  \n**Schema:** {st.session_state.snowflake_connection_params.get('schema')}  \n**Role:** {st.session_state.snowflake_connection_params.get('role')}")
    else:
        st.warning("Disconnected from Snowflake. Please connect to proceed.")

    st.markdown("---")
    st.header("Dashboard Filters")
    if not st.session_state.latest_dataframe.empty:
        df_columns = st.session_state.latest_dataframe.columns.tolist()
        
        # Clear existing filters button
        if st.button("Clear All Filters", key="clear_filters"):
            st.session_state.active_filters = {}
            st.rerun()

        for col in df_columns:
            if col not in st.session_state.active_filters: # Add filter only if not already present
                if st.button(f"Add Filter for {col}", key=f"add_filter_{col}"):
                    st.session_state.active_filters[col] = [] # Initialize with empty list
                    st.rerun()

        st.subheader("Active Filters")
        if not st.session_state.active_filters:
            st.info("No filters applied yet. Use 'Add Filter' buttons above.")

        for col, current_selection in list(st.session_state.active_filters.items()): # Use list to allow modification during iteration
            st.write(f"**{col}**")
            if pd.api.types.is_numeric_dtype(st.session_state.latest_dataframe[col]):
                min_val, max_val = float(st.session_state.latest_dataframe[col].min()), float(st.session_state.latest_dataframe[col].max())
                if not current_selection: # Set initial range if empty
                    current_selection = (min_val, max_val)
                selected_range = st.slider(
                    f"Select range for {col}",
                    min_value=min_val,
                    max_value=max_val,
                    value=current_selection if current_selection else (min_val, max_val),
                    key=f"filter_slider_{col}"
                )
                if selected_range != st.session_state.active_filters.get(col):
                    st.session_state.active_filters[col] = selected_range
            else:
                unique_values = st.session_state.latest_dataframe[col].unique().tolist()
                selected_values = st.multiselect(
                    f"Select values for {col}",
                    options=unique_values,
                    default=current_selection if current_selection else unique_values,
                    key=f"filter_multiselect_{col}"
                )
                if set(selected_values) != set(st.session_state.active_filters.get(col, [])):
                    st.session_state.active_filters[col] = selected_values

            if st.button(f"Remove Filter for {col}", key=f"remove_filter_{col}"):
                del st.session_state.active_filters[col]
                st.rerun()
    else:
        st.info("Execute a query first to enable dashboard filters.")


# --- Main Content Area ---
tab_sql, tab_dashboard = st.tabs(["SQL Editor & Results", "Dashboard"])

with tab_sql:
    st.header("SQL Query Editor")
    if st.session_state.connected_to_snowflake:
        query_text = st.text_area(
            "Enter your SQL query here:",
            value=st.session_state.latest_query_text,
            height=250,
            key="sql_editor_area"
        )

        col_exec, col_hist = st.columns([1, 4])
        with col_exec:
            if st.button("Execute Query", use_container_width=True):
                if query_text:
                    st.session_state.latest_query_text = query_text
                    st.session_state.latest_query_error = None # Clear previous error
                    try:
                        with st.spinner("Executing query..."):
                            df = execute_snowflake_query(query_text, st.session_state.snowflake_connection_params)
                        st.session_state.latest_dataframe = df
                        st.session_state.query_history.append(query_text)
                        st.success("Query executed successfully!")
                        if not df.empty:
                            st.info(f"Fetched {len(df)} rows and {len(df.columns)} columns.")
                        else:
                            st.warning("Query returned no data.")
                    except ValueError as e: # Catch SQL errors
                        st.session_state.latest_query_error = str(e)
                        st.error(f"SQL Execution Error: {e}")
                    except ConnectionError as e: # Catch connection errors within cached function
                        st.session_state.latest_query_error = str(e)
                        st.error(f"Connection Error: {e}. Please check your connection.")
                    except Exception as e:
                        st.session_state.latest_query_error = str(e)
                        st.error(f"An unexpected error occurred: {e}")
                else:
                    st.warning("Please enter a SQL query to execute.")
        with col_hist:
            if st.session_state.query_history:
                selected_history_query = st.selectbox(
                    "Query History",
                    options=[""] + list(reversed(st.session_state.query_history)),
                    index=0,
                    help="Select a past query to load it into the editor.",
                    key="query_history_select"
                )
                if selected_history_query and selected_history_query != st.session_state.latest_query_text:
                    st.session_state.latest_query_text = selected_history_query
                    st.rerun()
            else:
                st.info("No query history yet.")

        st.markdown("---")
        st.subheader("Query Results")
        if st.session_state.latest_query_error:
            st.error(st.session_state.latest_query_error)
        elif not st.session_state.latest_dataframe.empty:
            st.dataframe(st.session_state.latest_dataframe, use_container_width=True)
            
            # Export data button
            csv = st.session_state.latest_dataframe.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="snowflake_query_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Execute a query to see results here.")
    else:
        st.warning("Please connect to Snowflake in the sidebar to use the SQL editor.")


with tab_dashboard:
    st.header("Interactive Dashboard")

    if not st.session_state.latest_dataframe.empty:
        st.markdown("---")
        st.subheader("Add New Chart")
        
        # Increment key to reset form on successful chart addition
        chart_config_key = st.session_state.chart_config_key

        with st.form(key=f"chart_config_form_{chart_config_key}"):
            df_cols = st.session_state.latest_dataframe.columns.tolist()
            numeric_cols = st.session_state.latest_dataframe.select_dtypes(include=['number']).columns.tolist()
            object_cols = st.session_state.latest_dataframe.select_dtypes(include=['object', 'datetime']).columns.tolist()

            chart_type_options = ["Bar", "Line", "Area", "Scatter", "Pie", "KPI Metric"]
            selected_chart_type = st.selectbox("Chart Type", chart_type_options, key=f"chart_type_{chart_config_key}")

            if selected_chart_type == "KPI Metric":
                kpi_col = st.selectbox("Select Column for KPI", df_cols, key=f"kpi_col_{chart_config_key}")
                kpi_agg = st.selectbox("Aggregation", ["count", "sum", "mean", "min", "max"], key=f"kpi_agg_{chart_config_key}")
                kpi_title = st.text_input("KPI Title", value=f"{kpi_agg.capitalize()} of {kpi_col}", key=f"kpi_title_{chart_config_key}")
                chart_config = {
                    "chart_type": "kpi",
                    "column": kpi_col,
                    "aggregation": kpi_agg,
                    "title": kpi_title
                }
            else:
                col_x, col_y = st.columns(2)
                with col_x:
                    x_col = st.selectbox("X-axis (Categorical/Time)", df_cols, key=f"x_col_{chart_config_key}")
                with col_y:
                    y_col = st.selectbox("Y-axis (Quantitative)", numeric_cols if numeric_cols else df_cols, key=f"y_col_{chart_config_key}")

                color_col = st.selectbox("Color (Optional)", ["None"] + df_cols, key=f"color_col_{chart_config_key}")
                color_col = None if color_col == "None" else color_col

                agg_options = ["mean", "sum", "count", "min", "max"]
                y_agg = st.selectbox("Y-axis Aggregation", agg_options, key=f"y_agg_{chart_config_key}")

                chart_title = st.text_input("Chart Title", value=f"{selected_chart_type} of {y_agg.capitalize()} {y_col} by {x_col}", key=f"chart_title_{chart_config_key}")

                chart_config = {
                    "chart_type": selected_chart_type.lower(),
                    "x_col": x_col,
                    "y_col": y_col,
                    "color_col": color_col,
                    "title": chart_title,
                    "aggregation": y_agg
                }

            add_chart_button = st.form_submit_button("Add Chart to Dashboard")

            if add_chart_button:
                if selected_chart_type == "KPI Metric":
                    if kpi_col:
                        st.session_state.dashboard_charts.append(chart_config)
                        st.success(f"KPI Metric '{kpi_title}' added!")
                        st.session_state.chart_config_key += 1 # Reset form
                        st.rerun()
                    else:
                        st.warning("Please select a column for the KPI Metric.")
                else:
                    if x_col and y_col:
                        st.session_state.dashboard_charts.append(chart_config)
                        st.success(f"'{chart_title}' chart added!")
                        st.session_state.chart_config_key += 1 # Reset form
                        st.rerun()
                    else:
                        st.warning("Please select both X and Y axis columns.")
    else:
        st.info("Execute a SQL query first to generate visualizations.")

    st.markdown("---")
    st.subheader("Your Dashboard")

    if not st.session_state.dashboard_charts:
        st.info("No charts added to the dashboard yet. Add charts using the controls above.")
    else:
        filtered_df = apply_filters_to_dataframe(st.session_state.latest_dataframe, st.session_state.active_filters)
        
        # Use columns for a grid layout, max 2 charts per row
        cols_per_row = 2
        for i, chart_cfg in enumerate(st.session_state.dashboard_charts):
            if i % cols_per_row == 0:
                chart_cols = st.columns(cols_per_row)
            
            with chart_cols[i % cols_per_row]:
                st.expander(f"⚙️ {chart_cfg.get('title', 'Chart')}", expanded=False).button(
                    f"Remove '{chart_cfg.get('title', 'Chart')}'", 
                    key=f"remove_chart_{i}",
                    on_click=lambda idx=i: st.session_state.dashboard_charts.pop(idx)
                )

                if chart_cfg["chart_type"] == "kpi":
                    kpi_value = generate_kpi_metric(filtered_df, chart_cfg["column"], chart_cfg["aggregation"])
                    st.metric(label=chart_cfg["title"], value=kpi_value)
                else:
                    chart = generate_chart(filtered_df, chart_cfg)
                    if chart:
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.error(f"Could not render chart: {chart_cfg.get('title', 'Unknown Chart')}. Check configuration and data types.")