Okay, here's the complete `app.py` and `requirements.txt` for a professional, dark-themed Streamlit dashboard with all the specified features.

---

**`app.py`**

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import io
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="Sales Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Suppress SettingWithCopyWarning
pd.set_option('mode.chained_assignment', None)

# --- Custom Dark Modern UI CSS ---
st.markdown(
    """
    <style>
    /* General body styling */
    body {
        font-family: 'Inter', sans-serif; /* Modern font */
        background-color: #1a1a2e; /* Dark background */
        color: #e0e0e0; /* Light text */
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f0f1c; /* Slightly darker sidebar */
        color: #e0e0e0;
        padding: 1rem;
        border-right: 1px solid #2a2a4a;
    }

    [data-testid="stSidebar"] .stButton > button {
        background-color: #4a4e69;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 15px;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #5a5e79;
    }

    /* Header styling */
    h1, h2, h3, h4, h5, h6 {
        color: #bb86fc; /* A nice accent color for headers */
        font-weight: 600;
    }
    h1 {
        font-size: 2.5em;
        margin-bottom: 0.5em;
        border-bottom: 2px solid #3f3f5f;
        padding-bottom: 0.3em;
    }

    /* KPI cards styling */
    [data-testid="stMetric"] {
        background-color: #2a2a4a; /* Darker background for metrics */
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        margin-bottom: 15px;
        border: 1px solid #3f3f5f;
    }

    [data-testid="stMetricLabel"] div {
        color: #e0e0e0;
        font-size: 1.1em;
        font-weight: 500;
    }

    [data-testid="stMetricValue"] {
        color: #03dac6; /* A contrasting accent color for values */
        font-size: 2.2em !important;
        font-weight: 700;
    }

    [data-testid="stMetricDelta"] {
        color: #00e676 !important; /* Green for positive delta */
    }

    /* Plotly Chart container */
    .stPlotlyChart {
        background-color: #2a2a4a; /* Match KPI cards */
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border: 1px solid #3f3f5f;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        background-color: #2a2a4a;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #3f3f5f;
    }

    /* Multiselect/Selectbox styling */
    .stMultiSelect > div > div > div:first-child, .stSelectbox > div > div > div:first-child {
        background-color: #3f3f5f;
        color: #e0e0e0;
        border-radius: 5px;
        border: 1px solid #4a4e69;
    }
    .stMultiSelect div[data-testid="stOptions"], .stSelectbox div[data-testid="stOptions"] {
        background-color: #3f3f5f;
        border: 1px solid #4a4e69;
    }
    .stMultiSelect div[data-testid="stMultiSelectOption"], .stSelectbox div[data-testid="stSelectboxOption"] {
        color: #e0e0e0;
    }
    .stMultiSelect div[data-testid="stMultiSelectOption"]:hover, .stSelectbox div[data-testid="stSelectboxOption"]:hover {
        background-color: #4a4e69;
    }

    /* Date Input */
    .stDateInput div[data-testid="stDateInput-start"] div[role="textbox"],
    .stDateInput div[data-testid="stDateInput-end"] div[role="textbox"] {
        background-color: #3f3f5f;
        color: #e0e0e0;
        border-radius: 5px;
        border: 1px solid #4a4e69;
    }

    /* Text Input */
    .stTextInput > div > div > input {
        background-color: #3f3f5f;
        color: #e0e0e0;
        border-radius: 5px;
        border: 1px solid #4a4e69;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background-color: #03dac6; /* A strong accent color */
        color: #1a1a2e;
        border-radius: 5px;
        border: none;
        padding: 10px 15px;
        font-weight: bold;
    }
    .stDownloadButton > button:hover {
        background-color: #00e676; /* Slightly different on hover */
        color: #0f0f1c;
    }

    /* Hide Streamlit header/footer/menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sample Data (if no CSV uploaded) ---
@st.cache_data
def generate_sample_data():
    data = {
        'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                                '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                                '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                                '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05',
                                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10',
                                '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10']),
        'revenue': [1000, 1200, 1100, 1300, 1500,
                    800, 900, 950, 1000, 1100,
                    1500, 1600, 1700, 1800, 1900,
                    500, 600, 550, 700, 750,
                    1600, 1750, 1800, 1950, 2000,
                    900, 1000, 1100, 1200, 1300,
                    1800, 1900, 2000, 2100, 2200,
                    600, 700, 650, 800, 850],
        'users': [50, 60, 55, 65, 75,
                  40, 45, 48, 50, 55,
                  70, 75, 80, 85, 90,
                  25, 30, 28, 35, 38,
                  80, 88, 90, 95, 100,
                  45, 50, 55, 60, 65,
                  90, 95, 100, 105, 110,
                  30, 35, 32, 40, 42],
        'country': ['USA', 'USA', 'USA', 'USA', 'USA',
                    'Canada', 'Canada', 'Canada', 'Canada', 'Canada',
                    'UK', 'UK', 'UK', 'UK', 'UK',
                    'Germany', 'Germany', 'Germany', 'Germany', 'Germany',
                    'USA', 'USA', 'USA', 'USA', 'USA',
                    'Canada', 'Canada', 'Canada', 'Canada', 'Canada',
                    'UK', 'UK', 'UK', 'UK', 'UK',
                    'Germany', 'Germany', 'Germany', 'Germany', 'Germany']
    }
    df = pd.DataFrame(data)
    # Extend data for more dates/countries to make it more interesting
    from faker import Faker
    fake = Faker()
    more_data = []
    countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Australia', 'Japan', 'Brazil']
    for i in range(1, 60): # Two months of data
        date = (datetime(2023, 1, 1) + pd.Timedelta(days=i)).strftime('%Y-%m-%d')
        for country in countries:
            revenue = fake.random_int(min=500, max=5000)
            users = fake.random_int(min=20, max=200)
            more_data.append({'date': date, 'revenue': revenue, 'users': users, 'country': country})
    df_extended = pd.DataFrame(more_data)
    df_extended['date'] = pd.to_datetime(df_extended['date'])
    df = pd.concat([df, df_extended], ignore_index=True)
    df = df.sort_values('date').reset_index(drop=True)
    return df

@st.cache_data
def load_data(uploaded_file):
    """Loads data from CSV or uses sample data."""
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.error(f"Error reading CSV: {e}. Please ensure it's a valid CSV file.")
            st.stop()
    else:
        df = generate_sample_data()
        st.info("No CSV uploaded. Displaying sample data. Upload your CSV in the sidebar!")

    # Ensure required columns exist
    required_cols = ['date', 'revenue', 'users', 'country']
    if not all(col in df.columns for col in required_cols):
        st.error(f"CSV must contain the columns: {', '.join(required_cols)}")
        st.stop()

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

# --- Sidebar Filters ---
st.sidebar.title("Dashboard Filters")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

df = load_data(uploaded_file)

# Get unique countries and date range from the loaded data
all_countries = df['country'].unique().tolist()
min_date = df['date'].min().date()
max_date = df['date'].max().date()

selected_countries = st.sidebar.multiselect(
    "Select Countries",
    options=all_countries,
    default=all_countries
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Ensure date_range always has two elements
if len(date_range) == 2:
    start_date, end_date = date_range[0], date_range[1]
elif len(date_range) == 1:
    start_date, end_date = date_range[0], date_range[0] # Handle case where only one date is selected
else: # Default to full range if nothing is selected or invalid
    start_date, end_date = min_date, max_date


min_revenue = st.sidebar.slider(
    "Minimum Revenue",
    min_value=int(df['revenue'].min()),
    max_value=int(df['revenue'].max()),
    value=int(df['revenue'].min())
)

min_users = st.sidebar.slider(
    "Minimum Users",
    min_value=int(df['users'].min()),
    max_value=int(df['users'].max()),
    value=int(df['users'].min())
)

# Apply filters
df_filtered = df[
    (df['country'].isin(selected_countries)) &
    (df['date'].dt.date >= start_date) &
    (df['date'].dt.date <= end_date) &
    (df['revenue'] >= min_revenue) &
    (df['users'] >= min_users)
]

# Check if filtered dataframe is empty
if df_filtered.empty:
    st.error("No data available for the selected filters. Please adjust your selections.")
    st.stop() # Stop the app if no data

# --- Main Dashboard Content ---
st.title("📊 Sales Performance Dashboard")

# --- KPI Cards ---
st.subheader("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

total_revenue = df_filtered['revenue'].sum()
total_users = df_filtered['users'].sum()
avg_revenue_per_user = total_revenue / total_users if total_users > 0 else 0
num_countries = df_filtered['country'].nunique()

with col1:
    st.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")
with col2:
    st.metric(label="Total Users", value=f"{total_users:,}")
with col3:
    st.metric(label="Avg. Rev/User", value=f"${avg_revenue_per_user:,.2f}")
with col4:
    st.metric(label="Active Countries", value=num_countries)

st.markdown("---") # Separator

# --- Plotly Charts ---
st.subheader("Performance Trends & Distribution")

# Revenue Over Time
revenue_over_time = df_filtered.groupby('date')['revenue'].sum().reset_index()
fig_revenue_time = px.line(
    revenue_over_time,
    x='date',
    y='revenue',
    title='Revenue Over Time',
    labels={'revenue': 'Total Revenue', 'date': 'Date'},
    template="plotly_dark",
    line_shape="spline"
)
fig_revenue_time.update_traces(line_color='#03dac6', line_width=3)
fig_revenue_time.update_layout(hovermode="x unified")

# Users Over Time
users_over_time = df_filtered.groupby('date')['users'].sum().reset_index()
fig_users_time = px.line(
    users_over_time,
    x='date',
    y='users',
    title='Users Over Time',
    labels={'users': 'Total Users', 'date': 'Date'},
    template="plotly_dark",
    line_shape="spline"
)
fig_users_time.update_traces(line_color='#bb86fc', line_width=3)
fig_users_time.update_layout(hovermode="x unified")

col_charts_1, col_charts_2 = st.columns(2)
with col_charts_1:
    st.plotly_chart(fig_revenue_time, use_container_width=True)
with col_charts_2:
    st.plotly_chart(fig_users_time, use_container_width=True)

# Revenue by Country
revenue_by_country = df_filtered.groupby('country')['revenue'].sum().sort_values(ascending=False).reset_index()
fig_country_revenue = px.bar(
    revenue_by_country,
    x='country',
    y='revenue',
    title='Revenue by Country',
    labels={'revenue': 'Total Revenue', 'country': 'Country'},
    template="plotly_dark",
    color='revenue', # Color by revenue magnitude
    color_continuous_scale=px.colors.sequential.Viridis # Dark-friendly color scale
)
fig_country_revenue.update_layout(hovermode="x unified")

# Users by Country
users_by_country = df_filtered.groupby('country')['users'].sum().sort_values(ascending=False).reset_index()
fig_country_users = px.bar(
    users_by_country,
    x='country',
    y='users',
    title='Users by Country',
    labels={'users': 'Total Users', 'country': 'Country'},
    template="plotly_dark",
    color='users', # Color by users magnitude
    color_continuous_scale=px.colors.sequential.Plasma # Another dark-friendly color scale
)
fig_country_users.update_layout(hovermode="x unified")

col_charts_3, col_charts_4 = st.columns(2)
with col_charts_3:
    st.plotly_chart(fig_country_revenue, use_container_width=True)
with col_charts_4:
    st.plotly_chart(fig_country_users, use_container_width=True)

st.markdown("---")

# --- Search and Filtered Data Display ---
st.subheader("Detailed Data")

search_term = st.text_input("Search in data (all columns)", "")

df_display = df_filtered.copy() # Work on a copy for display

if search_term:
    # Search across all string columns
    df_display = df_display[
        df_display.apply(
            lambda row: row.astype(str).str.contains(search_term, case=False).any(),
            axis=1
        )
    ]

st.dataframe(df_display, use_container_width=True)

# --- Download CSV Button ---
@st.cache_data
def convert_df_to_csv(df):
    # IMPORTANT: Cache the conversion to avoid computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

if not df_display.empty:
    csv_data = convert_df_to_csv(df_display)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name='filtered_sales_data.csv',
        mime='text/csv',
    )
else:
    st.info("No data to download based on current filters and search.")
```

---

**`requirements.txt`**

```
streamlit==1.28.2
pandas==2.1.3
plotly==5.18.0
faker==20.0.0 # Added for more robust sample data generation
```

---

**How to Run the Dashboard:**

1.  **Save the files:**
    *   Save the first code block as `app.py`.
    *   Save the second code block as `requirements.txt`.
    *   Make sure both files are in the same directory.

2.  **Install dependencies:**
    Open your terminal or command prompt, navigate to the directory where you saved the files, and run:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit app:**
    Still in the same directory in your terminal, run:
    ```bash
    streamlit run app.py
    ```

    Your web browser should automatically open to the Streamlit dashboard.

**Features Implemented:**

*   **Dark Modern UI:** Custom CSS applied to achieve a sleek, dark aesthetic with accent colors for headers, metrics, and charts.
*   **Sidebar filters:**
    *   **Upload CSV:** Allows users to upload their own CSV with `date, revenue, users, country` columns.
    *   **Country Multiselect:** Filter data by selecting multiple countries.
    *   **Date Range Selector:** Choose a specific period using a date input.
    *   **Min Revenue/Users Sliders:** Filter based on minimum values for these metrics.
*   **KPI cards:** Displays `Total Revenue`, `Total Users`, `Average Revenue per User`, and `Active Countries` prominently at the top.
*   **Plotly charts:**
    *   **Line charts:** Revenue Over Time and Users Over Time, with `plotly_dark` template for consistency.
    *   **Bar charts:** Revenue by Country and Users by Country, also with `plotly_dark` template and color scales.
*   **Search and filtering:** A text input allows users to search across all columns in the displayed raw data.
*   **Responsive layout:** Uses `st.set_page_config(layout="wide")` and `st.columns` for an adaptive layout that works well on different screen sizes. `use_container_width=True` is used for charts and dataframe.
*   **Caching:**
    *   `@st.cache_data` is used for `load_data` to efficiently handle CSV uploads and default data.
    *   `@st.cache_data` is also used for `convert_df_to_csv` to optimize the download process.
*   **Download CSV button:** Allows users to download the currently filtered and searched data as a CSV file.
*   **Sample Data:** If no CSV is uploaded, the dashboard automatically loads and displays sample data generated using `faker` for demonstration.
*   **Error Handling:** Basic error handling for malformed CSVs and empty filtered dataframes.