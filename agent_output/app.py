import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import streamlit_authenticator as stauth
from PIL import Image
import os

# Authenticate
credentials = {
    "name": ["streamlit"],
    "key": ["12345"],
}

authenticator = stauth.authenticate(credentials, "My Streamlit App")
if authenticator:
    name = authenticator.name

# Set page configuration
st.set_page_config(layout="wide", page_title="My Streamlit App", page_icon=":bar_chart:")

# Function to load data
@st.cache(allow_output_mutation=True)
def load_data(file):
    return pd.read_csv(file)

# Load data
if 'data' not in st.session_state:
    st.session_state.data = None

# Sidebar
with st.sidebar:
    st.image("https://streamlit.io/images/ streamlit-logo-primary-colormark-darktext.png", width=100)
    st.title(":bar_chart: My Streamlit App")

    # Upload CSV file
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    # Filter by country
    if uploaded_file:
        data = load_data(uploaded_file)
        countries = data["country"].unique().tolist()
        country_filter = st.multiselect("Country", countries)
    else:
        country_filter = None

    # Filter by date
    start_date = st.date_input("Start Date", value=datetime.today().replace(day=1))
    end_date = st.date_input("End Date", value=datetime.today())

    # Download CSV button
    if 'data' in st.session_state and st.session_state.data is not None:
        if st.button("Download CSV"):
            @st.cache
            def convert_df(data):
                return data.to_csv().encode('utf-8')
            csv = convert_df(st.session_state.data)
            st.download_button("Download CSV", csv, "file.csv", "text/csv", key='download-csv')

# Main content
if uploaded_file:
    data = load_data(uploaded_file)

    # Save data to session
    st.session_state.data = data

    # Apply filters
    if country_filter:
        data = data[data["country"].isin(country_filter)]
    data = data[(data["date"] >= str(start_date)) & (data["date"] <= str(end_date))]

    # KPI cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue", f"${data['revenue'].sum():,.2f}")
    col2.metric("Users", f"{data['users'].sum():,}")
    col3.metric("Countries", f"{len(data['country'].unique())}")

    # Search and filtering
    search_term = st.text_input("Search")
    filtered_data = data[data["country"].str.contains(search_term, case=False)]

    # Plotly charts
    fig1 = px.bar(filtered_data, x="country", y="revenue", title="Revenue by Country")
    fig2 = px.line(filtered_data, x="date", y="users", title="Users Over Time")

    # Display charts
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Please upload a CSV file to get started.")