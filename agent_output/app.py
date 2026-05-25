import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import os
from dotenv import load_dotenv

# --- Configuration & Initialization ---

# 1. Load environment variables
load_dotenv()
APP_NAME = os.getenv("APP_NAME", "AI Agent Framework")

# 2. Setup Logging
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(LOGS_DIR, "app.log")),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

# 3. Streamlit Page Configuration
st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 4. Initialize Streamlit Session State
# This ensures state persists across reruns
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "chart_type" not in st.session_state:
    st.session_state.chart_type = "Bar Chart"
if "x_axis_col" not in st.session_state:
    st.session_state.x_axis_col = None
if "y_axis_col" not in st.session_state:
    st.session_state.y_axis_col = None
if "color_col" not in st.session_state:
    st.session_state.color_col = None
if "error_message" not in st.session_state:
    st.session_state.error_message = None

# --- Helper Functions ---

def display_error(message):
    """Displays an error message to the user and logs it."""
    st.session_state.error_message = message
    logger.error(message)
    st.error(message)

def clear_error():
    """Clears any existing error message."""
    st.session_state.error_message = None

def get_column_types(df):
    """Returns lists of column names by their inferred type."""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    return numeric_cols, categorical_cols, datetime_cols

def get_default_cols(df):
    """Attempts to find sensible default columns for charting."""
    numeric_cols, categorical_cols, _ = get_column_types(df)

    default_x = None
    if categorical_cols:
        default_x = categorical_cols[0]
    elif numeric_cols:
        default_x = numeric_cols[0]

    default_y = None
    if numeric_cols:
        default_y = numeric_cols[0]

    default_color = None
    if categorical_cols and len(categorical_cols) > 1:
        # Try to pick a different categorical col for color if available
        default_color = categorical_cols[1]
    elif categorical_cols and len(categorical_cols) == 1:
        default_color = categorical_cols[0] # If only one, use it
    
    return default_x, default_y, default_color

# --- UI Layout ---

st.title(f"{APP_NAME} 🤖")

# Sidebar for Navigation
st.sidebar.title(APP_NAME)
st.sidebar.markdown("---")
page_selection = st.sidebar.radio(
    "Go to",
    ["Home", "Data Explorer", "AI Agent Interaction"],
    index=["Home", "Data Explorer", "AI Agent Interaction"].index(st.session_state.current_page)
)

if page_selection != st.session_state.current_page:
    st.session_state.current_page = page_selection
    # Clear any data/chart state when navigating
    st.session_state.uploaded_df = None
    st.session_state.x_axis_col = None
    st.session_state.y_axis_col = None
    st.session_state.color_col = None
    clear_error()
    st.experimental_rerun() # Force rerun to clear main content


# --- Main Content Area ---

if st.session_state.current_page == "Home":
    st.header("Welcome to the AI Agent Framework!")
    st.write("""
        This application provides a foundational framework for an AI Agent project.
        Use the sidebar to navigate through different sections:
        - **Data Explorer**: Upload your data (CSV/Excel) and visualize it with interactive charts.
        - **AI Agent Interaction**: A placeholder for future AI agent interfaces.
        
        Get started by exploring your data!
    """)
    st.image("https://via.placeholder.com/600x200?text=AI+Agent+Framework+Dashboard", caption="Future AI Agent Dashboard Preview")

elif st.session_state.current_page == "Data Explorer":
    st.header("Data Explorer 📊")
    st.write("Upload your CSV or Excel file to visualize and explore your data.")

    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1]
        
        try:
            if file_extension == "csv":
                df = pd.read_csv(uploaded_file)
            elif file_extension == "xlsx":
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            else:
                display_error("Unsupported file type. Please upload a CSV or XLSX file.")
                st.session_state.uploaded_df = None # Clear df on error
                st.stop() # Stop execution if file type is wrong

            st.session_state.uploaded_df = df.copy() # Store a copy in session state
            clear_error()
            logger.info(f"Successfully uploaded and parsed '{uploaded_file.name}' with {len(df)} rows and {len(df.columns)} columns.")

        except Exception as e:
            display_error(f"Error reading file: {e}. Please ensure it's a valid CSV/Excel format.")
            st.session_state.uploaded_df = None # Clear df on error
    
    if st.session_state.uploaded_df is not None:
        df = st.session_state.uploaded_df
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True)

        st.subheader("Chart Generator")
        
        all_columns = df.columns.tolist()
        numeric_cols, categorical_cols, _ = get_column_types(df)

        # Set sensible defaults if not already set or if columns changed
        if st.session_state.x_axis_col not in all_columns:
            st.session_state.x_axis_col, st.session_state.y_axis_col, st.session_state.color_col = get_default_cols(df)
            
        col1, col2, col3 = st.columns(3)

        with col1:
            st.session_state.chart_type = st.selectbox(
                "Select Chart Type",
                ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"],
                key="chart_type_select"
            )

        with col2:
            # X-axis for all charts, try to default to first categorical
            st.session_state.x_axis_col = st.selectbox(
                "Select X-axis/Category Column",
                options=[None] + all_columns,
                index=([None] + all_columns).index(st.session_state.x_axis_col) if st.session_state.x_axis_col in all_columns else 0,
                key="x_axis_select"
            )

        with col3:
            # Y-axis/Value for non-Pie charts, or Color for all
            if st.session_state.chart_type in ["Bar Chart", "Line Chart", "Scatter Plot"]:
                st.session_state.y_axis_col = st.selectbox(
                    "Select Y-axis/Value Column",
                    options=[None] + numeric_cols, # Y-axis usually numeric
                    index=([None] + numeric_cols).index(st.session_state.y_axis_col) if st.session_state.y_axis_col in numeric_cols else 0,
                    key="y_axis_select"
                )
            elif st.session_state.chart_type == "Pie Chart":
                st.session_state.y_axis_col = st.selectbox(
                    "Select Value Column (for Pie slice sizes)",
                    options=[None] + numeric_cols,
                    index=([None] + numeric_cols).index(st.session_state.y_axis_col) if st.session_state.y_axis_col in numeric_cols else 0,
                    key="pie_value_select"
                )
        
        # Color column applicable to all chart types
        st.session_state.color_col = st.selectbox(
            "Select Color Column (Optional)",
            options=[None] + categorical_cols + numeric_cols, # Can color by numeric too
            index=([None] + categorical_cols + numeric_cols).index(st.session_state.color_col) if st.session_state.color_col in (categorical_cols + numeric_cols) else 0,
            key="color_col_select"
        )
        
        # --- Chart Generation Logic ---
        fig = None
        
        try:
            if st.session_state.x_axis_col and st.session_state.y_axis_col:
                # Common parameters for plotly express
                chart_params = {
                    "data_frame": df,
                    "x": st.session_state.x_axis_col,
                    "color": st.session_state.color_col,
                    "title": f"{st.session_state.chart_type} of {st.session_state.y_axis_col} by {st.session_state.x_axis_col}"
                }

                if st.session_state.chart_type == "Bar Chart":
                    if st.session_state.y_axis_col not in numeric_cols:
                        display_error("For Bar Chart, Y-axis must be numeric.")
                    else:
                        fig = px.bar(y=st.session_state.y_axis_col, **chart_params)
                
                elif st.session_state.chart_type == "Line Chart":
                    if st.session_state.y_axis_col not in numeric_cols:
                        display_error("For Line Chart, Y-axis must be numeric.")
                    else:
                        fig = px.line(y=st.session_state.y_axis_col, **chart_params)

                elif st.session_state.chart_type == "Scatter Plot":
                    if st.session_state.y_axis_col not in numeric_cols:
                        display_error("For Scatter Plot, Y-axis must be numeric.")
                    else:
                        fig = px.scatter(y=st.session_state.y_axis_col, **chart_params)
                
                elif st.session_state.chart_type == "Pie Chart":
                    if st.session_state.x_axis_col not in (categorical_cols + numeric_cols) or st.session_state.y_axis_col not in numeric_cols:
                        display_error("For Pie Chart, Category (names) can be any type, but Value (values) must be numeric.")
                    else:
                        fig = px.pie(df, names=st.session_state.x_axis_col, values=st.session_state.y_axis_col,
                                     color=st.session_state.color_col,
                                     title=f"Pie Chart of {st.session_state.y_axis_col} by {st.session_state.x_axis_col}")
                
                if fig:
                    clear_error()
                    st.plotly_chart(fig, use_container_width=True)
            elif st.session_state.x_axis_col is None or st.session_state.y_axis_col is None:
                st.info("Please select both X-axis/Category and Y-axis/Value columns to generate a chart.")

        except ValueError as ve:
            display_error(f"Chart generation error: {ve}. Please check your column selections for the chosen chart type.")
        except Exception as e:
            display_error(f"An unexpected error occurred during chart generation: {e}")
            logger.exception("Unexpected error during chart generation.")

    else:
        st.info("Upload a file to get started with data exploration!")


elif st.session_state.current_page == "AI Agent Interaction":
    st.header("AI Agent Interaction Area 💬")
    st.write("""
        This section will host the interface for interacting with various AI agents.
        You can input queries, view responses, and manage agent interactions here.
        **(Currently a placeholder - actual agent logic will be integrated in future updates.)**
    """)

    st.text_area("Agent Input:", height=150, placeholder="Type your query for the AI agent here...")
    st.button("Send to Agent")

    st.subheader("Agent Response")
    st.info("No agent response yet. This will display the AI agent's output.")

# Display persistent error message if any
if st.session_state.error_message:
    st.error(st.session_state.error_message)

st.sidebar.markdown("---")
st.sidebar.info(f"App Version: 0.1.0")