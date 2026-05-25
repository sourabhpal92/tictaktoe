Okay, let's create a professional Streamlit dashboard with all the specified requirements.

First, here's the `requirements.txt` file:

**`requirements.txt`**
```
streamlit
pandas
plotly
openpyxl # For robust CSV/Excel handling if needed, though pandas is usually enough for CSV
```

Next, here's the complete `app.py` code:

**`app.py`**
```python
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom dark modern CSS
st.markdown(
    """
    <style>
    /* Main container background */
    .stApp {
        background-color: #1a1a2e; /* Dark background */
        color: #e0e0e0; /* Light text */
    }

    /* Sidebar background */
    .st-emotion-cache-1ldf0i7 { /* Targets the sidebar container */
        background-color: #16213e; /* Slightly darker than main */
    }

    /* Headers and Titles */
    h1, h2, h3, h4, h5, h6 {
        color: #e0e0e0;
    }

    /* Text */
    p, label, .stMarkdown {
        color: #c0c0c0;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #2c394b;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #0f3460;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    [data-testid="stMetric"] > div:first-child {
        color: #87CEEB; /* Light blue for the label */
        font-weight: bold;
    }
    [data-testid="stMetric"] > div:nth-child(2) > div:first-child {
        color: #F7D04B; /* Yellow for the value */
        font-size: 2.5em;
        font-weight: bold;
    }

    /* Buttons */
    .stButton > button {
        background-color: #0f3460;
        color: #e0e0e0;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #1a5e9a;
        color: #ffffff;
    }

    /* Selectbox / Multiselect / Date input */
    .st-emotion-cache-10asx4q, .st-emotion-cache-f1g0i0 { /* Targets the input containers */
        background-color: #2c394b;
        color: #e0e0e0;
        border-radius: 5px;
        border: 1px solid #0f3460;
    }
    .st-emotion-cache-10asx4q input, .st-emotion-cache-f1g0i0 input {
        color: #e0e0e0;
    }
    .st-emotion-cache-10asx4q div[data-baseweb="select"] {
        background-color: #2c394b; /* Dropdown background */
        color: #e0e0e0;
    }
    .st-emotion-cache-10asx4q div[data-baseweb="select"] > div:first-child {
        color: #e0e0e0;
    }
    .st-emotion-cache-10asx4q div[data-baseweb="select"] div[role="listbox"] {
        background-color: #2c394b; /* Dropdown options background */
        color: #e0e0e0;
    }
    .st-emotion-cache-10asx4q div[data-baseweb="select"] div[role="option"] {
        color: #e0e0e0;
    }
    .st-emotion-cache-10asx4q div[data-baseweb="select"] div[role="option"]:hover {
        background-color: #0f3460;
        color: #ffffff;
    }
    
    /* Table/DataFrame */
    .st-emotion-cache-fxl5ga { /* Targets the DataFrame container */
        border: 1px solid #0f3460;
        border-radius: 10px;
        background-color: #2c394b;
    }

    /* Plotly chart container styling (optional, plotly itself has themes) */
    .block-container .element-container {
        border-radius: 10px;
        padding: 10px;
        background-color: #2c394b; /* Slightly lighter background for chart container */
        border: 1px solid #0f3460;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }

    /* Text Input */
    .stTextInput>div>div>input {
        background-color: #2c394b;
        color: #e0e0e0;
        border: 1px solid #0f3460;
        border-radius: 5px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --- 2. DATA LOADING & CACHING ---
@st.cache_data
def load_data(uploaded_file):
    """Loads CSV data from an uploaded file."""
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            # Ensure required columns exist
            required_cols = ['date', 'revenue', 'users', 'country']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Error: Missing one or more required columns. Please ensure your CSV has: {', '.join(required_cols)}")
                return pd.DataFrame(columns=required_cols) # Return empty DataFrame with expected columns

            # Convert 'date' column to datetime
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df.dropna(subset=['date'], inplace=True) # Drop rows where date conversion failed
            
            # Ensure numeric columns are actually numeric
            df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
            df['users'] = pd.to_numeric(df['users'], errors='coerce').fillna(0)

            # Sort by date
            df = df.sort_values('date').reset_index(drop=True)
            return df
        except Exception as e:
            st.error(f"Error loading file: {e}. Please ensure it's a valid CSV.")
            return pd.DataFrame(columns=['date', 'revenue', 'users', 'country'])
    return pd.DataFrame(columns=['date', 'revenue', 'users', 'country']) # Empty DataFrame if no file

# Helper function to generate dummy data (for initial testing if no file uploaded)
def generate_dummy_data():
    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
    countries = ['USA', 'Canada', 'Mexico', 'UK', 'Germany', 'France']
    
    data = []
    for date in dates:
        for country in countries:
            revenue = abs(round(100 + date.day * 5 + date.month * 10 + pd.np.random.normal(0, 20), 2))
            users = abs(round(10 + date.day + pd.np.random.normal(0, 5)))
            data.append([date, revenue, users, country])
            
    df = pd.DataFrame(data, columns=['date', 'revenue', 'users', 'country'])
    return df

# --- 3. SIDEBAR FILTERS ---
st.sidebar.title("Configuration")

uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.sidebar.info("No file uploaded. Using dummy data for demonstration.")
    df = generate_dummy_data()
    # Create a dummy file object for potential download, if needed. Not strictly necessary for dummy data.

if df.empty:
    st.warning("No data available to display. Please upload a valid CSV.")
    st.stop() # Stop the app if no data


st.sidebar.header("Data Filters")

# Country filter
all_countries = ['All'] + sorted(df['country'].unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=['All']
)

# Date range filter
min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date)
)

# Ensure date_range has two dates
if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])
else:
    # If only one date is selected, assume it's the start date and end date is the same
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[0])


# Apply filters
filtered_df = df[
    (df['date'] >= start_date) & 
    (df['date'] <= end_date)
]

if 'All' not in selected_countries:
    filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]

# --- 4. MAIN DASHBOARD LAYOUT ---
st.title("📊 Sales Performance Dashboard")
st.markdown("Monitor your key sales metrics and trends.")

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --- KPI Cards ---
st.header("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

total_revenue = filtered_df['revenue'].sum()
total_users = filtered_df['users'].sum()
avg_revenue_per_user = total_revenue / total_users if total_users > 0 else 0
num_countries = filtered_df['country'].nunique()

with col1:
    st.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")
with col2:
    st.metric(label="Total Users", value=f"{total_users:,.0f}")
with col3:
    st.metric(label="Avg. Revenue/User", value=f"${avg_revenue_per_user:,.2f}")
with col4:
    st.metric(label="Active Countries", value=f"{num_countries}")

st.markdown("---")

# --- Plotly Charts ---
st.header("Sales Trends & Distribution")

# Daily Trend Chart (Revenue & Users)
st.subheader("Daily Revenue and User Trends")
daily_summary = filtered_df.groupby('date').agg(
    total_revenue=('revenue', 'sum'),
    total_users=('users', 'sum')
).reset_index()

fig_daily_trend = px.line(
    daily_summary,
    x='date',
    y=['total_revenue', 'total_users'],
    title='Daily Revenue and Users',
    labels={'value': 'Amount', 'variable': 'Metric', 'date': 'Date'},
    height=400,
    template="plotly_dark"
)
fig_daily_trend.update_layout(
    xaxis_title="Date",
    yaxis_title="Value",
    legend_title="Metric",
    hovermode="x unified",
    margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig_daily_trend, use_container_width=True)

# Revenue by Country Bar Chart
st.subheader("Revenue by Country")
revenue_by_country = filtered_df.groupby('country')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)

fig_country_revenue = px.bar(
    revenue_by_country,
    x='country',
    y='revenue',
    title='Total Revenue by Country',
    labels={'revenue': 'Total Revenue', 'country': 'Country'},
    color='revenue', # Color bars based on revenue
    color_continuous_scale=px.colors.sequential.Plasma, # A nice color scale for dark theme
    height=400,
    template="plotly_dark"
)
fig_country_revenue.update_layout(
    xaxis_title="Country",
    yaxis_title="Total Revenue",
    margin=dict(l=20, r=20, t=50, b=20)
)
st.plotly_chart(fig_country_revenue, use_container_width=True)

st.markdown("---")

# --- Search and Filtering for Data Table ---
st.header("Detailed Data View")

search_term = st.text_input("Search in data (e.g., 'USA', '2023-01-15')", "")

if search_term:
    search_filtered_df = filtered_df[
        filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
    ]
    st.dataframe(search_filtered_df, use_container_width=True, hide_index=True)
else:
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)


# --- Download CSV Button ---
@st.cache_data
def convert_df_to_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

st.markdown("---")
st.subheader("Download Data")

# Create a file-like object in memory for the CSV
csv_data = convert_df_to_csv(filtered_df)

st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name=f"sales_dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv",
    help="Download the currently displayed filtered data as a CSV file."
)

st.sidebar.markdown("---")
st.sidebar.markdown("Developed with ❤️ using Streamlit")
```

---

### How to Run:

1.  **Save the files:**
    *   Save the `requirements.txt` content as `requirements.txt` in your project folder.
    *   Save the `app.py` content as `app.py` in the same project folder.

2.  **Create a dummy `data.csv` (optional, for testing without upload):**
    If you want to test the app without immediately uploading a CSV, you can create a simple `data.csv` in the same directory:

    **`data.csv`**
    ```csv
    date,revenue,users,country
    2023-01-01,1500,50,USA
    2023-01-01,800,30,Canada
    2023-01-02,1700,55,USA
    2023-01-02,900,32,Canada
    2023-01-03,2000,60,USA
    2023-01-03,1100,35,Mexico
    2023-01-04,1200,40,UK
    2023-01-04,1800,58,USA
    2023-01-05,2500,70,Germany
    2023-01-05,1300,42,France
    2023-01-06,1600,52,USA
    2023-01-06,950,33,Canada
    2023-01-07,2100,65,Germany
    2023-01-07,1400,45,UK
    2023-01-08,1900,60,Mexico
    2023-01-08,1000,30,France
    2023-01-09,2200,68,USA
    2023-01-09,1150,38,Canada
    2023-01-10,2300,70,Germany
    2023-01-10,1250,40,France
    ```
    *Note: The app will use generated dummy data if no file is uploaded, so `data.csv` is not strictly required.*

3.  **Install dependencies:**
    Open your terminal or command prompt, navigate to your project folder, and run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

This will open the dashboard in your web browser, presenting a dark-themed, interactive sales dashboard with the specified features!