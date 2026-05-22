Here's the complete Streamlit application code (`app.py`) and its corresponding `requirements.txt` file, fulfilling all your requirements.

This dashboard provides a modern dark UI, allows users to upload their CSV, dynamically filters data, displays key performance indicators (KPIs), visualizes trends with Plotly charts, and enables downloading the filtered data.

---

### `app.py` (Main Streamlit Application File)

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import io
import numpy as np # Used for generating sample data

# --- Page Configuration ---
st.set_page_config(
    page_title="Sales & User Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    theme="dark" # Sets the dark modern UI theme
)

# --- Caching Functions ---

@st.cache_data
def get_initial_data():
    """
    Generates a dummy dataset for initial load if no CSV is uploaded.
    This ensures the app runs immediately for demonstration.
    """
    np.random.seed(42) # for reproducibility
    start_date = pd.to_datetime('2023-01-01')
    end_date = pd.to_datetime('2023-12-31')
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    data = {
        'date': dates,
        'revenue': np.random.randint(1000, 15000, len(dates)) + np.random.randn(len(dates)) * 500,
        'users': np.random.randint(50, 800, len(dates)) + np.random.randn(len(dates)) * 50,
        'country': np.random.choice(['USA', 'Canada', 'Mexico', 'UK', 'Germany', 'France', 'Japan', 'Australia'], len(dates))
    }
    df = pd.DataFrame(data)
    # Ensure revenue and users are positive integers
    df['revenue'] = df['revenue'].apply(lambda x: max(100, round(x))).astype(int)
    df['users'] = df['users'].apply(lambda x: max(10, round(x))).astype(int)
    return df

@st.cache_data
def load_csv_data(file_buffer):
    """
    Loads and preprocesses CSV data from an uploaded file.
    Caches the result to avoid re-loading on every interaction.
    """
    df = pd.read_csv(file_buffer)
    
    # Validate required columns
    required_cols = ['date', 'revenue', 'users', 'country']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Uploaded CSV must contain the following columns: {', '.join(required_cols)}")
        st.stop() # Stop execution if essential columns are missing
        
    df['date'] = pd.to_datetime(df['date'])
    return df

# --- Sidebar Filters ---
with st.sidebar:
    st.header("Configuration Panel")
    
    st.markdown("Upload your CSV file with `date`, `revenue`, `users`, and `country` columns.")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    
    df = None
    if uploaded_file is not None:
        try:
            df = load_csv_data(uploaded_file)
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            st.stop() # Stop if there's a problem loading the file
    else:
        st.info("No CSV uploaded. Using sample data for demonstration. Upload your own data to begin!")
        df = get_initial_data()

    # If df is still None (e.g., error during upload), stop
    if df is None:
        st.warning("Please upload a valid CSV file to proceed.")
        st.stop()

    st.subheader("Date Range Selection")
    # Ensure min/max dates are in date format for the slider
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    date_range = st.slider(
        "Select a date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date), # Default to full range
        format="YYYY-MM-DD"
    )
    
    # Convert slider output back to datetime for filtering
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    
    st.subheader("Country Filter")
    all_countries = sorted(df['country'].unique())
    selected_countries = st.multiselect(
        "Select countries",
        options=all_countries,
        default=all_countries # Default to all selected for initial view
    )

    # Apply filters to the DataFrame
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    if selected_countries: # Only filter by country if selections are made
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
    else:
        st.warning("Please select at least one country to display data.")
        # If no countries are selected, display an empty DataFrame to avoid errors downstream
        filtered_df = pd.DataFrame(columns=df.columns) 

# --- Main Dashboard Content ---
st.title("📈 Sales & User Performance Dashboard")
st.markdown("A comprehensive look at revenue and user trends, powered by your data.")

if filtered_df.empty:
    st.info("No data available for the selected filters. Please adjust your selections in the sidebar.")
else:
    # --- KPI Cards ---
    st.header("Key Performance Indicators")
    
    # Calculate KPIs
    total_revenue = filtered_df['revenue'].sum()
    total_users = filtered_df['users'].sum()
    
    # Calculate daily averages for more stable KPIs
    daily_revenue_summary = filtered_df.groupby('date')['revenue'].sum()
    avg_daily_revenue = daily_revenue_summary.mean() if not daily_revenue_summary.empty else 0
    
    avg_revenue_per_user = total_revenue / total_users if total_users > 0 else 0
    
    # Display KPIs in columns
    col1, col2, col3, col4 = st.columns(4) 
    
    with col1:
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    with col2:
        st.metric("Total Users", f"{total_users:,.0f}")
    with col3:
        st.metric("Avg. Rev per User", f"${avg_revenue_per_user:,.2f}")
    with col4:
        st.metric("Avg. Daily Revenue", f"${avg_daily_revenue:,.2f}")

    # --- Plotly Charts ---
    st.header("Visualizations")
    
    # Aggregate data for daily trends
    daily_summary = filtered_df.groupby('date').agg(
        total_revenue=('revenue', 'sum'),
        total_users=('users', 'sum')
    ).reset_index()

    if not daily_summary.empty:
        # Time Series Charts
        col_chart_time1, col_chart_time2 = st.columns(2)
        with col_chart_time1:
            st.subheader("Revenue Over Time")
            fig_revenue_time = px.line(
                daily_summary,
                x='date',
                y='total_revenue',
                title='Daily Revenue Trend',
                labels={'total_revenue': 'Revenue ($)'},
                template="plotly_dark" # Use dark theme for plotly charts
            )
            fig_revenue_time.update_traces(mode='lines+markers', marker=dict(size=4))
            st.plotly_chart(fig_revenue_time, use_container_width=True)

        with col_chart_time2:
            st.subheader("Users Over Time")
            fig_users_time = px.line(
                daily_summary,
                x='date',
                y='total_users',
                title='Daily Active Users Trend',
                labels={'total_users': 'Users'},
                template="plotly_dark"
            )
            fig_users_time.update_traces(mode='lines+markers', marker=dict(size=4))
            st.plotly_chart(fig_users_time, use_container_width=True)
            
    # Aggregate data for country breakdown
    country_summary = filtered_df.groupby('country').agg(
        total_revenue=('revenue', 'sum'),
        total_users=('users', 'sum')
    ).reset_index().sort_values(by='total_revenue', ascending=False)
    
    if not country_summary.empty:
        # Bar Charts for Country Breakdown
        col_chart_country1, col_chart_country2 = st.columns(2)
        with col_chart_country1:
            st.subheader("Revenue by Country")
            fig_rev_country = px.bar(
                country_summary,
                x='country',
                y='total_revenue',
                title='Total Revenue by Country',
                labels={'total_revenue': 'Revenue ($)'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_rev_country, use_container_width=True)

        with col_chart_country2:
            st.subheader("Users by Country")
            fig_users_country = px.bar(
                country_summary,
                x='country',
                y='total_users',
                title='Total Users by Country',
                labels={'total_users': 'Users'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_users_country, use_container_width=True)

    # --- Raw Data & Download ---
    st.header("Filtered Raw Data")
    # st.dataframe provides built-in search/filtering capabilities
    st.dataframe(filtered_df, use_container_width=True)

    # Convert filtered DataFrame to CSV for download
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv_data,
        file_name="filtered_sales_data.csv",
        mime="text/csv",
        help="Click to download the currently filtered data as a CSV file."
    )

```

---

### `requirements.txt`

```
streamlit
pandas
plotly
numpy
```

---

### How to Run the Application:

1.  **Save the files:**
    *   Save the first code block as `app.py`.
    *   Save the second code block as `requirements.txt`.
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

Your web browser will automatically open the Streamlit dashboard, initially populated with sample data. You can then upload your own CSV file, filter the data using the sidebar controls, view KPIs and charts, and download the filtered dataset.