import streamlit as st
import pandas as pd
import snowflake.connector
import os
import json
import plotly.graph_objects as go
import plotly.express as px
import uuid # For unique chart IDs

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Snowflake Analytics Dashboard", page_icon="❄️")

# --- Session State Initialization ---
if 'is_connected' not in st.session_state:
    st.session_state.is_connected = False
if 'current_snowflake_config' not in st.session_state:
    st.session_state.current_snowflake_config = {
        "account": "", "user": "", "password": "",
        "warehouse": "", "database": "", "schema": "", "role": ""
    }
if 'sql_query_editor_content' not in st.session_state:
    st.session_state.sql_query_editor_content = "SELECT CURRENT_VERSION() AS SNOWFLAKE_VERSION;"
if 'last_query_results' not in st.session_state:
    st.session_state.last_query_results = {"dataframe": pd.DataFrame(), "query": "", "timestamp": None, "error": None}
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'dashboard_charts' not in st.session_state:
    st.session_state.dashboard_charts = []
if 'dashboard_filters' not in st.session_state:
    st.session_state.dashboard_filters = {} # {column: [selected_values]}

# --- Helper Functions ---

def _get_secrets():
    """Reads Snowflake credentials from st.secrets or environment variables."""
    # Prioritize st.secrets (for Streamlit Cloud deployment)
    if 'snowflake' in st.secrets:
        return st.secrets['snowflake']
    
    # Fallback to environment variables (for local development)
    return {
        "account": os.environ.get("SNOWFLAKE_ACCOUNT", ""),
        "user": os.environ.get("SNOWFLAKE_USER", ""),
        "password": os.environ.get("SNOWFLAKE_PASSWORD", ""),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", ""),
        "database": os.environ.get("SNOWFLAKE_DATABASE", ""),
        "schema": os.environ.get("SNOWFLAKE_SCHEMA", ""),
        "role": os.environ.get("SNOWFLAKE_ROLE", "")
    }

@st.cache_resource(ttl=3600) # Cache connection for 1 hour
def get_snowflake_connection(account, user, password, warehouse, database, schema, role):
    """Establishes and returns a Snowflake connection."""
    try:
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema,
            role=role,
            client_session_keep_alive=True # Keep session alive
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to Snowflake: {e}")
        return None

@st.cache_data(ttl=600) # Cache metadata for 10 minutes
def get_snowflake_metadata(conn, query_type):
    """Fetches Snowflake metadata (warehouses, databases, schemas, roles)."""
    if not conn:
        return []
    
    cursor = conn.cursor()
    try:
        if query_type == "warehouses":
            cursor.execute("SHOW WAREHOUSES")
        elif query_type == "databases":
            cursor.execute("SHOW DATABASES")
        elif query_type == "schemas":
            cursor.execute("SHOW SCHEMAS")
        elif query_type == "roles":
            cursor.execute("SHOW ROLES")
        else:
            return []
        
        results = cursor.fetchall()
        # Extract name from the result tuple (often the 2nd element)
        if query_type == "warehouses":
            return [row[0] for row in results if row[0].upper() != 'SNOWFLAKE'] # Exclude SNOWFLAKE_WAREHOUSE
        elif query_type == "databases":
            return [row[1] for row in results]
        elif query_type == "schemas":
            return [row[1] for row in results]
        elif query_type == "roles":
            return [row[0] for row in results]

    except Exception as e:
        st.warning(f"Could not fetch {query_type}: {e}")
        return []
    finally:
        cursor.close()

@st.cache_data(ttl=600, show_spinner="Executing query and fetching data...") # Cache query results for 10 minutes
def execute_sql(conn, query_string, query_limit=None):
    """Executes an SQL query and returns a Pandas DataFrame."""
    if not conn:
        return pd.DataFrame(), "No active Snowflake connection."

    if query_limit and query_limit > 0:
        query_string_with_limit = f"{query_string.strip()}{'' if query_string.strip().endswith(';') else ';'} LIMIT {query_limit}"
    else:
        query_string_with_limit = query_string

    cursor = conn.cursor()
    try:
        cursor.execute(query_string_with_limit)
        df = cursor.fetch_pandas_all()
        return df, None
    except snowflake.connector.errors.ProgrammingError as e:
        return pd.DataFrame(), f"Snowflake Query Error: {e.msg}"
    except Exception as e:
        return pd.DataFrame(), f"An unexpected error occurred: {e}"
    finally:
        cursor.close()

def clear_all_caches():
    """Clears Streamlit's data and resource caches."""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("All caches cleared!")

def apply_dashboard_filters(df, filters):
    """Applies active dashboard filters to a DataFrame."""
    if not filters or df.empty:
        return df
    
    filtered_df = df.copy()
    for column, selected_values in filters.items():
        if column in filtered_df.columns and selected_values:
            # Handle numerical filters if needed, currently assumes categorical
            filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
    return filtered_df

# --- Sidebar UI ---
with st.sidebar:
    st.title("❄️ Snowflake Dashboard")

    st.subheader("Connection Settings")
    
    secrets = _get_secrets()
    
    st.session_state.current_snowflake_config["account"] = st.text_input(
        "Account Identifier", value=secrets.get("account", ""), 
        help="e.g., ab12345.eu-central-1"
    )
    st.session_state.current_snowflake_config["user"] = st.text_input(
        "User", value=secrets.get("user", "")
    )
    st.session_state.current_snowflake_config["password"] = st.text_input(
        "Password", type="password", value=secrets.get("password", "")
    )

    if st.button("Connect to Snowflake", use_container_width=True):
        config = st.session_state.current_snowflake_config
        conn = get_snowflake_connection(
            config["account"], config["user"], config["password"], 
            config["warehouse"], config["database"], config["schema"], config["role"]
        )
        if conn:
            st.session_state.is_connected = True
            st.success("Successfully connected to Snowflake!")
            # Fetch initial metadata
            st.session_state.current_snowflake_config["warehouse"] = get_snowflake_metadata(conn, "warehouses")[0] if get_snowflake_metadata(conn, "warehouses") else ""
            st.session_state.current_snowflake_config["database"] = get_snowflake_metadata(conn, "databases")[0] if get_snowflake_metadata(conn, "databases") else ""
            st.session_state.current_snowflake_config["schema"] = get_snowflake_metadata(conn, "schemas")[0] if get_snowflake_metadata(conn, "schemas") else ""
            st.session_state.current_snowflake_config["role"] = get_snowflake_metadata(conn, "roles")[0] if get_snowflake_metadata(conn, "roles") else ""
            
        else:
            st.session_state.is_connected = False
            st.error("Connection failed. Check your credentials.")

    if st.session_state.is_connected:
        conn_active = get_snowflake_connection(
            st.session_state.current_snowflake_config["account"],
            st.session_state.current_snowflake_config["user"],
            st.session_state.current_snowflake_config["password"],
            st.session_state.current_snowflake_config["warehouse"],
            st.session_state.current_snowflake_config["database"],
            st.session_state.current_snowflake_config["schema"],
            st.session_state.current_snowflake_config["role"]
        )
        
        st.session_state.current_snowflake_config["warehouse"] = st.selectbox(
            "Warehouse",
            options=get_snowflake_metadata(conn_active, "warehouses"),
            index=0 if get_snowflake_metadata(conn_active, "warehouses") else None,
            key="sb_warehouse"
        )
        st.session_state.current_snowflake_config["database"] = st.selectbox(
            "Database",
            options=get_snowflake_metadata(conn_active, "databases"),
            index=0 if get_snowflake_metadata(conn_active, "databases") else None,
            key="sb_database"
        )
        st.session_state.current_snowflake_config["schema"] = st.selectbox(
            "Schema",
            options=get_snowflake_metadata(conn_active, "schemas"),
            index=0 if get_snowflake_metadata(conn_active, "schemas") else None,
            key="sb_schema"
        )
        st.session_state.current_snowflake_config["role"] = st.selectbox(
            "Role",
            options=get_snowflake_metadata(conn_active, "roles"),
            index=0 if get_snowflake_metadata(conn_active, "roles") else None,
            key="sb_role"
        )

        st.markdown("---")
        st.subheader("Dashboard Filters")
        if st.session_state.dashboard_charts:
            # Collect all unique columns from the dataframes used in charts
            all_cols = set()
            for chart_spec in st.session_state.dashboard_charts:
                if 'data' in chart_spec and not chart_spec['data'].empty:
                    all_cols.update(chart_spec['data'].columns.tolist())
            
            if all_cols:
                for col in sorted(list(all_cols)):
                    unique_values = st.session_state.dashboard_charts[0]['data'][col].unique().tolist() # Use first chart's data as base
                    
                    if len(unique_values) <= 50: # Only show filters for columns with a reasonable number of unique values
                        selected_vals = st.multiselect(f"Filter by {col}", options=unique_values, key=f"filter_{col}")
                        if selected_vals:
                            st.session_state.dashboard_filters[col] = selected_vals
                        elif col in st.session_state.dashboard_filters:
                            del st.session_state.dashboard_filters[col] # Remove filter if selection is empty
            else:
                st.info("Execute a query and add charts to enable dashboard filters.")
        else:
            st.info("Add charts to the dashboard to enable filters.")

        st.markdown("---")
        st.subheader("Query History")
        if st.session_state.query_history:
            for i, entry in enumerate(reversed(st.session_state.query_history)):
                with st.expander(f"Query {len(st.session_state.query_history) - i}: {entry['status'].capitalize()} at {entry['timestamp'].strftime('%H:%M:%S')}"):
                    st.code(entry['query'])
                    if entry['error']:
                        st.error(entry['error'])
                    if st.button(f"Load Query {len(st.session_state.query_history) - i}", key=f"load_query_{i}"):
                        st.session_state.sql_query_editor_content = entry['query']
                        st.experimental_rerun()
        else:
            st.info("No queries executed yet.")
            
    st.markdown("---")
    if st.button("Clear All Caches", type="secondary", use_container_width=True):
        clear_all_caches()
        st.session_state.is_connected = False # Reset connection state after clearing resource cache
        st.session_state.dashboard_charts = []
        st.session_state.query_history = []
        st.experimental_rerun()

# --- Main Content ---
tab_sql_editor, tab_dashboard = st.tabs(["SQL Editor", "Dashboard"])

with tab_sql_editor:
    st.header("SQL Query Editor")

    query_limit_input = st.number_input("Max rows to fetch (0 for no limit)", min_value=0, value=1000, step=100)
    
    st.session_state.sql_query_editor_content = st.text_area(
        "Enter your SQL query", 
        st.session_state.sql_query_editor_content, 
        height=300
    )

    col_execute, col_add_chart = st.columns([1, 1])

    with col_execute:
        if st.button("Execute Query", type="primary", use_container_width=True):
            if not st.session_state.is_connected:
                st.warning("Please connect to Snowflake first in the sidebar.")
            elif not st.session_state.sql_query_editor_content.strip():
                st.warning("Please enter an SQL query.")
            else:
                conn_exec = get_snowflake_connection(
                    st.session_state.current_snowflake_config["account"],
                    st.session_state.current_snowflake_config["user"],
                    st.session_state.current_snowflake_config["password"],
                    st.session_state.current_snowflake_config["warehouse"],
                    st.session_state.current_snowflake_config["database"],
                    st.session_state.current_snowflake_config["schema"],
                    st.session_state.current_snowflake_config["role"]
                )
                if conn_exec:
                    df, error = execute_sql(conn_exec, st.session_state.sql_query_editor_content, query_limit=query_limit_input)
                    st.session_state.last_query_results = {
                        "dataframe": df,
                        "query": st.session_state.sql_query_editor_content,
                        "timestamp": pd.Timestamp.now(),
                        "error": error
                    }
                    st.session_state.query_history.append({
                        "query": st.session_state.sql_query_editor_content,
                        "timestamp": pd.Timestamp.now(),
                        "status": "failure" if error else "success",
                        "error": error
                    })
                    if error:
                        st.error(error)
                    else:
                        st.success(f"Query executed successfully. Fetched {len(df)} rows.")
                else:
                    st.error("Could not get an active connection to execute query.")

    if not st.session_state.last_query_results['dataframe'].empty:
        st.subheader("Query Results")
        st.dataframe(st.session_state.last_query_results['dataframe'], use_container_width=True)

        available_columns = st.session_state.last_query_results['dataframe'].columns.tolist()

        with col_add_chart:
            if st.button("Add Chart to Dashboard", type="secondary", use_container_width=True):
                if available_columns:
                    st.session_state.show_add_chart_modal = True
                else:
                    st.warning("No data available to create a chart.")

        if st.session_state.get('show_add_chart_modal', False):
            with st.expander("Configure New Chart", expanded=True):
                chart_title = st.text_input("Chart Title", f"Chart {len(st.session_state.dashboard_charts) + 1}")
                chart_type = st.selectbox(
                    "Chart Type",
                    options=["Bar Chart", "Line Chart", "Area Chart", "Scatter Chart", "Pie Chart", "Histogram", "Metric"],
                    key="new_chart_type"
                )
                
                x_col = None
                y_col = None
                color_col = None
                aggregate_func = None
                value_col = None # For Metric

                if chart_type in ["Bar Chart", "Line Chart", "Area Chart", "Scatter Chart"]:
                    x_col = st.selectbox("X-axis Column", options=available_columns, key="new_chart_x")
                    y_col = st.selectbox("Y-axis Column", options=available_columns, key="new_chart_y")
                    if chart_type == "Bar Chart":
                        aggregate_func = st.selectbox(
                            "Aggregation for Y-axis", 
                            options=["sum", "mean", "median", "count", "min", "max"],
                            key="new_chart_agg_bar"
                        )
                    
                elif chart_type == "Pie Chart":
                    names_col = st.selectbox("Category Column", options=available_columns, key="new_chart_pie_names")
                    values_col = st.selectbox("Value Column", options=available_columns, key="new_chart_pie_values")
                    x_col = names_col # Map to generic x_col for consistency
                    y_col = values_col # Map to generic y_col for consistency

                elif chart_type == "Histogram":
                    x_col = st.selectbox("Column to analyze", options=available_columns, key="new_chart_hist_x")

                elif chart_type == "Metric":
                    value_col = st.selectbox("Value Column", options=available_columns, key="new_chart_metric_value")
                    aggregate_func = st.selectbox(
                        "Aggregation for Metric", 
                        options=["sum", "mean", "median", "count", "min", "max"],
                        key="new_chart_agg_metric"
                    )

                if st.button("Save Chart to Dashboard"):
                    chart_spec = {
                        "id": str(uuid.uuid4()),
                        "title": chart_title,
                        "chart_type": chart_type,
                        "x_col": x_col,
                        "y_col": y_col,
                        "color_col": color_col,
                        "aggregate_func": aggregate_func,
                        "value_col": value_col,
                        "source_query": st.session_state.last_query_results['query'],
                        "data": st.session_state.last_query_results['dataframe'].copy() # Store a copy of the dataframe
                    }
                    st.session_state.dashboard_charts.append(chart_spec)
                    st.session_state.show_add_chart_modal = False
                    st.success(f"Chart '{chart_title}' added to dashboard!")
                    st.experimental_rerun()
    else:
        st.info("Execute a query to see results and add charts to the dashboard.")


with tab_dashboard:
    st.header("Interactive Dashboard")

    if not st.session_state.dashboard_charts:
        st.info("No charts added to the dashboard yet. Go to the 'SQL Editor' tab to execute queries and add charts.")
    else:
        num_charts = len(st.session_state.dashboard_charts)
        
        # Determine columns layout (e.g., 2 charts per row)
        cols = st.columns(2) if num_charts > 1 else st.columns(1)
        
        for i, chart_spec in enumerate(st.session_state.dashboard_charts):
            current_col = cols[i % len(cols)]
            with current_col:
                with st.container(border=True):
                    st.subheader(chart_spec['title'])
                    
                    # Apply filters to the chart's data
                    filtered_df = apply_dashboard_filters(chart_spec['data'], st.session_state.dashboard_filters)

                    if filtered_df.empty:
                        st.warning("No data to display after applying filters.")
                        if st.button(f"Remove Chart '{chart_spec['title']}'", key=f"remove_chart_{chart_spec['id']}", type="secondary"):
                            st.session_state.dashboard_charts.pop(i)
                            st.experimental_rerun()
                        continue

                    if chart_spec['chart_type'] == "Bar Chart":
                        if chart_spec['x_col'] and chart_spec['y_col']:
                            # For aggregation, group by x_col and apply func to y_col
                            if chart_spec['aggregate_func']:
                                aggregated_data = filtered_df.groupby(chart_spec['x_col'])[chart_spec['y_col']].agg(chart_spec['aggregate_func']).reset_index()
                                st.bar_chart(aggregated_data, x=chart_spec['x_col'], y=chart_spec['y_col'])
                            else:
                                st.bar_chart(filtered_df, x=chart_spec['x_col'], y=chart_spec['y_col'])
                        else: st.warning("Chart configuration incomplete.")
                    
                    elif chart_spec['chart_type'] == "Line Chart":
                        if chart_spec['x_col'] and chart_spec['y_col']:
                            st.line_chart(filtered_df, x=chart_spec['x_col'], y=chart_spec['y_col'])
                        else: st.warning("Chart configuration incomplete.")

                    elif chart_spec['chart_type'] == "Area Chart":
                        if chart_spec['x_col'] and chart_spec['y_col']:
                            st.area_chart(filtered_df, x=chart_spec['x_col'], y=chart_spec['y_col'])
                        else: st.warning("Chart configuration incomplete.")

                    elif chart_spec['chart_type'] == "Scatter Chart":
                        if chart_spec['x_col'] and chart_spec['y_col']:
                            st.scatter_chart(filtered_df, x=chart_spec['x_col'], y=chart_spec['y_col'])
                        else: st.warning("Chart configuration incomplete.")
                    
                    elif chart_spec['chart_type'] == "Pie Chart":
                        if chart_spec['x_col'] and chart_spec['y_col']: # x_col is names, y_col is values
                            fig = px.pie(
                                filtered_df, 
                                names=chart_spec['x_col'], 
                                values=chart_spec['y_col'], 
                                title=chart_spec['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else: st.warning("Chart configuration incomplete.")

                    elif chart_spec['chart_type'] == "Histogram":
                        if chart_spec['x_col']:
                            fig = px.histogram(
                                filtered_df, 
                                x=chart_spec['x_col'], 
                                title=chart_spec['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else: st.warning("Chart configuration incomplete.")

                    elif chart_spec['chart_type'] == "Metric":
                        if chart_spec['value_col'] and chart_spec['aggregate_func']:
                            try:
                                aggregated_value = getattr(filtered_df[chart_spec['value_col']], chart_spec['aggregate_func'])()
                                st.metric(label=chart_spec['title'], value=f"{aggregated_value:,.2f}")
                            except Exception as e:
                                st.error(f"Error calculating metric: {e}")
                        else: st.warning("Chart configuration incomplete.")
                    
                    if st.button(f"Remove Chart", key=f"remove_chart_button_{chart_spec['id']}", type="secondary"):
                        st.session_state.dashboard_charts = [c for c in st.session_state.dashboard_charts if c['id'] != chart_spec['id']]
                        st.experimental_rerun()