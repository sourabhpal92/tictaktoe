import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# App configuration
st.set_page_config(layout="wide", page_title="Revenue Dashboard", initial_sidebar_state="expanded")

# Load dataset from CSV
@st.cache
def load_data(file):
    return pd.read_csv(file)

# Create UI
st.markdown("# Revenue Dashboard")

# Sidebar filters
st.sidebar.title("Filters")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
country_filter = st.sidebar.multiselect("Country", options=None, default=None)
date_filter = st.sidebar.date_input("Date", value=None, key="date_filter")

if uploaded_file is not None:
    data = load_data(uploaded_file)
else:
    # Sample data for testing
    data = pd.DataFrame({
        "date": ["2022-01-01", "2022-01-02", "2022-01-03", "2022-01-04", "2022-01-05"],
        "revenue": [100, 200, 300, 400, 500],
        "users": [10, 20, 30, 40, 50],
        "country": ["USA", "Canada", "USA", "Canada", "USA"]
    })

# Update country filter options
if data is not None:
    country_filter_options = data["country"].unique()
    country_filter = st.sidebar.multiselect("Country", options=country_filter_options, default=country_filter or country_filter_options)

# Apply filters to data
if data is not None:
    if country_filter is not None and len(country_filter) > 0:
        data = data[data["country"].isin(country_filter)]
    
    if date_filter is not None:
        data["date"] = pd.to_datetime(data["date"])
        start_date = pd.to_datetime(date_filter)
        data = data[data["date"].dt.date == start_date.date()]

# KPI cards
st.write("### Key Performance Indicators (KPIs)")
col1, col2, col3 = st.columns(3)
col1.metric(label="Total Revenue", value=f"${data['revenue'].sum():,.2f}")
col2.metric(label="Total Users", value=f"{data['users'].sum():,}")
col3.metric(label="Average Revenue per User", value=f"${data['revenue'].sum() / data['users'].sum():,.2f}")

# Plotly charts
st.write("### Revenue and Users Over Time")
fig = px.line(data, x="date", y=["revenue", "users"])
st.plotly_chart(fig, use_container_width=True)

st.write("### Revenue by Country")
fig = px.pie(data, values="revenue", names="country")
st.plotly_chart(fig, use_container_width=True)

# Search and filtering
st.write("### Data Table")
if data is not None:
    data_table = data.copy()
    data_table["date"] = data_table["date"].astype(str)
    st.table(data_table)

# Download CSV button
st.write("### Download CSV")
if data is not None:
    @st.cache
    def convert_df(df):
        return df.to_csv(index=False)
    csv = convert_df(data)
    st.download_button(label="Download CSV", data=csv, file_name="data.csv", mime="text/csv")