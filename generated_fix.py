import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import streamlit.components.v1 as components
import io

# Configuration
st.set_page_config(layout="wide")

# Caching function
@st.cache
def load_data(file):
    return pd.read_csv(file)

# Load data
def load_default_data():
    return load_data("data.csv")

# App layout
st.markdown(
    """
    <style>
    /* Remove the main panel container */
    .css-1d391kg {
        background-color: #2c3e50;
        padding: 3rem 1rem;
        border-radius: 0.5rem;
        box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
    }
    /* Remove the streamlit branding */
    .css-v37k9u {
        visibility: hidden;
    }
    /* Center the title */
    .css-1d391kg h1 {
        text-align: center;
    }
    /* Change font size of title */
    .css-1d391kg h1 {
        font-size: 40px;
    }
    /* Change font color of title */
    .css-1d391kg h1 {
        color: #9b9b9b;
    }
    /* Change background color of sidebar */
    .css-17eq0n8 {
        background-color: #2c3e50;
    }
    /* Change text color of sidebar */
    .css-17eq0n8 label {
        color: #9b9b9b;
    }
    /* Change background color of sidebar options */
    .css-17eq0n8 div {
        background-color: #2c3e50;
    }
    /* Change color of sidebar options on hover */
    .css-17eq0n8 div:hover {
        background-color: #3c506a;
    }
    /* Change text color of options when selected */
    .css-1n1u75i {
        color: #9b9b9b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Title and header
st.header("Revenue Dashboard")

# Sidebar filters
st.sidebar.markdown(
    """
    <style>
    .css-17eq0n8 {
        background-color: #2c3e50;
    }
    .css-17eq0n8 label {
        color: #9b9b9b;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.sidebar.title("Filters")
country = st.sidebar.selectbox("Country", ["All", "USA", "Canada", "UK"])
if country == "All":
    country_filter = False
else:
    country_filter = country

start_date = st.sidebar.date_input("Start Date", datetime(2022, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime(2022, 12, 31))

# Upload CSV support
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

# Load dataset
if uploaded_file is not None:
    data = load_data(uploaded_file)
else:
    data = load_default_data()

# Apply filters
if country_filter:
    data = data[data["country"] == country_filter]
data = data[(data["date"] >= start_date) & (data["date"] <= end_date)]

# KPI cards
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Revenue", f"${data['revenue'].sum():,.0f}")
kpi2.metric("Total Users", f"{data['users'].sum():,.0f}")
kpi3.metric("Average Revenue per User", f"${data['revenue'].sum() / data['users'].sum():,.2f}")

# Plotly charts
fig1 = px.line(data, x="date", y="revenue", title="Revenue Over Time")
fig1.update_layout(
    xaxis_title="Date",
    yaxis_title="Revenue",
    font=dict(size=14),
    template="plotly_dark",
)
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.line(data, x="date", y="users", title="Users Over Time")
fig2.update_layout(
    xaxis_title="Date",
    yaxis_title="Users",
    font=dict(size=14),
    template="plotly_dark",
)
st.plotly_chart(fig2, use_container_width=True)

# Search and filtering
search_term = st.text_input("Search for a country", "")
if search_term:
    filtered_data = data[data["country"].str.contains(search_term, case=False)]
else:
    filtered_data = data

# Display filtered data
st.subheader("Data")
st.write(filtered_data)

# Download CSV button
@st.cache
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(filtered_data)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="data.csv",
    mime="text/csv",
)