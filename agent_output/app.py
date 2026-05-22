import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Set page configuration
st.set_page_config(
    page_title="Revenue Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to load data
@st.cache(allow_output_mutation=True)
def load_data(file):
    return pd.read_csv(file)

# Function to filter data
def filter_data(df, country, start_date, end_date):
    filtered_df = df.copy()
    if country:
        filtered_df = filtered_df[filtered_df['country'].isin(country)]
    if start_date:
        filtered_df = filtered_df[filtered_df['date'] >= start_date]
    if end_date:
        filtered_df = filtered_df[filtered_df['date'] <= end_date]
    return filtered_df

# Create dashboard
def create_dashboard(df):
    # Create sidebar
    with st.sidebar:
        st.title("Filters")
        country = st.multiselect(
            "Country",
            df['country'].unique(),
            default=df['country'].unique()
        )
        start_date = st.date_input(
            "Start Date",
            min_value=df['date'].min(),
            max_value=df['date'].max(),
            value=df['date'].min()
        )
        end_date = st.date_input(
            "End Date",
            min_value=df['date'].min(),
            max_value=df['date'].max(),
            value=df['date'].max()
        )
        file = st.file_uploader(
            "Upload CSV",
            type="csv",
            help="Upload a CSV file to update the dashboard"
        )
        if st.button("Download CSV"):
            @st.cache
            def convert_df(df):
                return df.to_csv().encode('utf-8')
            csv = convert_df(filtered_df)
            st.download_button(
                "Download CSV",
                csv,
                "data.csv",
                "text/csv",
                key='download-csv'
            )

    # Filter data
    filtered_df = filter_data(df, country, start_date, end_date)

    # Create KPI cards
    col1, col2, col3 = st.columns(3)
    with col1:
        kpi1 = st.card(
            "Revenue",
            value=f"${filtered_df['revenue'].sum():,.2f}"
        )
    with col2:
        kpi2 = st.card(
            "Users",
            value=f"{filtered_df['users'].sum():,}"
        )
    with col3:
        kpi3 = st.card(
            "Countries",
            value=f"{len(country)}"
        )

    # Create charts
    st.subheader("Revenue Over Time")
    revenue_fig = px.line(
        filtered_df,
        x="date",
        y="revenue",
        title="Revenue Over Time"
    )
    st.plotly_chart(revenue_fig, use_container_width=True)

    st.subheader("Users Over Time")
    users_fig = px.line(
        filtered_df,
        x="date",
        y="users",
        title="Users Over Time"
    )
    st.plotly_chart(users_fig, use_container_width=True)

    st.subheader("Country Breakdown")
    country_fig = px.pie(
        filtered_df,
        values="revenue",
        names="country",
        title="Country Breakdown"
    )
    st.plotly_chart(country_fig, use_container_width=True)

# Load initial data
if os.path.exists("data.csv"):
    df = load_data("data.csv")
else:
    df = pd.DataFrame({
        "date": ["2022-01-01", "2022-01-02", "2022-01-03"],
        "revenue": [100, 200, 300],
        "users": [10, 20, 30],
        "country": ["USA", "Canada", "Mexico"]
    })

# Create dashboard
create_dashboard(df)

# Update data if file is uploaded
if st.sidebar.file_uploader:
    file = st.sidebar.file_uploader
    if file is not None:
        df = load_data(file)
        create_dashboard(df)